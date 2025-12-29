from collections import defaultdict
import json
import traceback
from abc import abstractmethod
from asyncio import Lock, Task, create_task, gather, Semaphore, Event as AsyncIOEvent, sleep
from datetime import timedelta, datetime
from itertools import cycle
from logging import Logger
from typing import AsyncIterator, Optional, Sequence, Type, TypeVar
from aiohttp import web

from aiokafka import TopicPartition
from aiokafka.coordinator.assignors.abstract import AbstractPartitionAssignor
from aiokafka.coordinator.assignors.roundrobin import RoundRobinPartitionAssignor

from buz.event import Event
from buz.event.async_consumer import AsyncConsumer
from buz.event.exceptions.worker_execution_exception import WorkerExecutionException
from buz.event.infrastructure.buz_kafka.consume_strategy.consume_strategy import KafkaConsumeStrategy
from buz.event.infrastructure.buz_kafka.kafka_event_subscriber_executor import KafkaEventSubscriberExecutor
from buz.event.infrastructure.models.consuming_task import ConsumingTask
from buz.event.meta_subscriber import MetaSubscriber
from buz.kafka.domain.models.auto_create_topic_configuration import AutoCreateTopicConfiguration
from buz.kafka.domain.models.consumer_initial_offset_position import ConsumerInitialOffsetPosition
from buz.kafka.domain.models.kafka_connection_config import KafkaConnectionConfig
from buz.kafka.domain.models.kafka_poll_record import KafkaPollRecord
from buz.kafka.domain.services.kafka_admin_client import KafkaAdminClient
from buz.kafka.infrastructure.aiokafka.aiokafka_consumer import AIOKafkaConsumer
from buz.queue.in_memory.in_memory_multiqueue_repository import InMemoryMultiqueueRepository
from buz.queue.multiqueue_repository import MultiqueueRepository

T = TypeVar("T", bound=Event)


class BaseBuzAIOKafkaAsyncConsumer(AsyncConsumer):
    __FALLBACK_PARTITION_ASSIGNORS = (RoundRobinPartitionAssignor,)
    __DEFAULT_MAX_POLL_INTERVAL = 30 * 60 * 1000
    __DEFAULT_SESSION_TIMEOUT_MS = 1000 * 120
    __DEFAULT_HEARTBEAT_INTERVAL = int(__DEFAULT_SESSION_TIMEOUT_MS / 5)
    __SECONDS_BETWEEN_EXECUTIONS_IF_THERE_ARE_NO_TASKS_IN_THE_QUEUE = 1
    __SECONDS_BETWEEN_POLLS_IF_THERE_ARE_TASKS_IN_THE_QUEUE = 1
    __SECONDS_BETWEEN_POLLS_IF_THERE_ARE_NO_NEW_TASKS = 1
    __SECONDS_TO_WAIT_BETWEEN_REBALANCING_IN_PROGRESS = 0.1
    __MAX_NUMBER_OF_CONCURRENT_POLLING_TASKS = 20

    def __init__(
        self,
        *,
        connection_config: KafkaConnectionConfig,
        kafka_admin_client: Optional[KafkaAdminClient],
        consume_strategy: KafkaConsumeStrategy,
        max_queue_size: int,
        max_records_retrieved_per_poll: int,
        kafka_partition_assignors: tuple[Type[AbstractPartitionAssignor], ...] = (),
        subscribers: Sequence[MetaSubscriber],
        logger: Logger,
        health_check_port: Optional[int],
        consumer_initial_offset_position: ConsumerInitialOffsetPosition,
        auto_create_topic_configuration: Optional[AutoCreateTopicConfiguration] = None,
        seconds_between_executions_if_there_are_no_tasks_in_the_queue: Optional[int] = None,
        seconds_between_polls_if_there_are_tasks_in_the_queue: Optional[int] = None,
        seconds_between_polls_if_there_are_no_new_tasks: Optional[int] = None,
        max_number_of_concurrent_polling_tasks: Optional[int] = None,
        session_timeout_ms: Optional[int] = None,
        max_poll_interval_ms: Optional[int] = None,
        heartbeat_interval_ms: Optional[int] = None,
        wait_for_connection_to_cluster_ms: Optional[int] = None,
        worker_instance_id: Optional[str] = None,
        milliseconds_between_retries: int = 5000,
    ):
        self.__connection_config = connection_config
        self.__consume_strategy = consume_strategy
        self.__kafka_partition_assignors = kafka_partition_assignors
        self.__subscribers = subscribers
        self._logger = logger
        self.__health_check_port = health_check_port
        self.__consumer_initial_offset_position = consumer_initial_offset_position
        self.__executor_per_consumer_mapper: dict[AIOKafkaConsumer, KafkaEventSubscriberExecutor] = {}
        self.__queue_per_consumer_mapper: dict[
            AIOKafkaConsumer, MultiqueueRepository[TopicPartition, KafkaPollRecord]
        ] = {}
        self.__max_records_retrieved_per_poll: int = max_records_retrieved_per_poll
        self.__session_timeout_ms: int = session_timeout_ms or self.__DEFAULT_SESSION_TIMEOUT_MS
        self.__max_poll_interval_ms: int = max_poll_interval_ms or self.__DEFAULT_MAX_POLL_INTERVAL
        self.__heartbeat_interval_ms: int = heartbeat_interval_ms or self.__DEFAULT_HEARTBEAT_INTERVAL
        self.__max_queue_size: int = max_queue_size
        self.__should_stop: AsyncIOEvent = AsyncIOEvent()
        self.__start_kafka_consumers_elapsed_time: Optional[timedelta] = None
        self.__initial_coroutines_created_elapsed_time: Optional[timedelta] = None
        self.__events_processed: int = 0
        self.__events_processed_elapsed_time: timedelta = timedelta()
        self.__kafka_admin_client: Optional[KafkaAdminClient] = kafka_admin_client
        self.__auto_create_topic_configuration: Optional[AutoCreateTopicConfiguration] = auto_create_topic_configuration
        self.__seconds_between_executions_if_there_are_no_tasks_in_the_queue: int = (
            seconds_between_executions_if_there_are_no_tasks_in_the_queue
            or self.__SECONDS_BETWEEN_EXECUTIONS_IF_THERE_ARE_NO_TASKS_IN_THE_QUEUE
        )
        self.__seconds_between_polls_if_there_are_tasks_in_the_queue: int = (
            seconds_between_polls_if_there_are_tasks_in_the_queue
            or self.__SECONDS_BETWEEN_POLLS_IF_THERE_ARE_TASKS_IN_THE_QUEUE
        )
        self.__seconds_between_polls_if_there_are_no_new_tasks: int = (
            seconds_between_polls_if_there_are_no_new_tasks or self.__SECONDS_BETWEEN_POLLS_IF_THERE_ARE_NO_NEW_TASKS
        )
        self.__max_number_of_concurrent_polling_tasks: int = (
            max_number_of_concurrent_polling_tasks or self.__MAX_NUMBER_OF_CONCURRENT_POLLING_TASKS
        )
        self.__wait_for_connection_to_cluster_ms: Optional[int] = wait_for_connection_to_cluster_ms
        self.__worker_instance_id: Optional[str] = worker_instance_id
        self.__milliseconds_between_retries: int = milliseconds_between_retries
        self.__polling_tasks_semaphore = Semaphore(self.__max_number_of_concurrent_polling_tasks)
        self.__consumer_and_partition_mutex: dict[str, Lock] = defaultdict(Lock)
        self.__is_worked_initialized = False
        self.__number_of_rebalancing_processes_in_progress: int = 0

    async def configure_http_check_server(self, health_check_port: int) -> web.TCPSite:
        self._logger.info(f"Starting health check server on port {health_check_port}")
        app = web.Application()
        app.router.add_get("/health", self.__health_check)
        app.router.add_get("/ready", self.__is_ready)

        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", health_check_port)
        await site.start()
        return site

    async def run(self) -> None:
        self.__print_worker_configuration()
        start_time = datetime.now()
        health_check_server: Optional[web.TCPSite] = None

        if self.__health_check_port is not None:
            health_check_server = await self.configure_http_check_server(self.__health_check_port)

        await self.__generate_kafka_consumers()

        self.__initial_coroutines_created_elapsed_time = datetime.now() - start_time

        if len(self.__executor_per_consumer_mapper) == 0:
            self._logger.error("There are no valid subscribers to execute, finalizing consumer")
            return

        self.__is_worked_initialized = True

        start_consumption_time = datetime.now()
        worker_errors = await self.__run_worker()
        self.__events_processed_elapsed_time = datetime.now() - start_consumption_time

        await self.__handle_graceful_stop(worker_errors)

        if health_check_server is not None:
            await health_check_server.stop()

    def __print_worker_configuration(self) -> None:
        self._logger.info(
            f"Consumer configuration:\n"
            f"  - Worker instance id: {self.__worker_instance_id}\n"
            f"  - Consume strategy: {self.__consume_strategy}\n"
            f"  - Max queue size: {self.__max_queue_size}\n"
            f"  - Max records retrieved per poll: {self.__max_records_retrieved_per_poll}\n"
            f"  - Kafka partition assignors: {self.__kafka_partition_assignors}\n"
            f"  - Consumer initial offset position: {self.__consumer_initial_offset_position}\n"
            f"  - Session timeout ms: {self.__session_timeout_ms}\n"
            f"  - Max poll interval ms: {self.__max_poll_interval_ms}\n"
            f"  - Heartbeat interval ms: {self.__heartbeat_interval_ms}\n"
            f"  - Seconds between executions if there are no tasks in the queue: {self.__seconds_between_executions_if_there_are_no_tasks_in_the_queue}\n"
            f"  - Seconds between polls if there are tasks in the queue: {self.__seconds_between_polls_if_there_are_tasks_in_the_queue}\n"
            f"  - Seconds between polls if there are no new tasks: {self.__seconds_between_polls_if_there_are_no_new_tasks}\n"
            f"  - Max number of concurrent polling tasks: {self.__max_number_of_concurrent_polling_tasks}\n"
            f"  - Wait for connection to cluster ms: {self.__wait_for_connection_to_cluster_ms}\n"
            f"  - Milliseconds between retries: {self.__milliseconds_between_retries}ms ({self.__milliseconds_between_retries / 1000.0}s)\n"
            f"  - Health check port: {self.__health_check_port}\n"
            f"  - Number of subscribers: {len(self.__subscribers)}",
        )

    async def __handle_graceful_stop(self, worker_errors: tuple[Optional[Exception], Optional[Exception]]) -> None:
        self._logger.info("Stopping kafka consumers...")
        await self.__manage_kafka_consumers_stopping()
        self._logger.info("All kafka consumers stopped")

        self.__print_statistics()

        if self.__exceptions_are_thrown(worker_errors):
            consume_events_exception, polling_task_exception = worker_errors
            raise WorkerExecutionException(
                "The worker was closed by an unexpected exception"
            ) from consume_events_exception or polling_task_exception

    async def __run_worker(self) -> tuple[Optional[Exception], Optional[Exception]]:
        consume_events_task = create_task(self.__consume_events_task())
        polling_task = create_task(self.__polling_task())

        try:
            await gather(consume_events_task, polling_task)
            return (None, None)
        except Exception:
            self.__should_stop.set()
            consume_events_exception = await self.__await_exception(consume_events_task)
            polling_task_exception = await self.__await_exception(polling_task)
            return (consume_events_exception, polling_task_exception)

    async def __await_exception(self, task: Task) -> Optional[Exception]:
        try:
            await task
            return None
        except Exception as exception:
            return exception

    def __exceptions_are_thrown(self, worker_errors: tuple[Optional[Exception], Optional[Exception]]) -> bool:
        return any([error is not None for error in worker_errors])

    async def __generate_kafka_consumers(self):
        start_time = datetime.now()
        tasks = [self.__generate_kafka_consumer_for_subscriber(subscriber) for subscriber in self.__subscribers]
        await gather(*tasks)
        self.__start_kafka_consumers_elapsed_time = datetime.now() - start_time

    async def __generate_kafka_consumer_for_subscriber(self, subscriber: MetaSubscriber) -> None:
        executor = await self._create_kafka_consumer_executor(subscriber)
        topics = self.__consume_strategy.get_topics(subscriber)
        kafka_consumer = AIOKafkaConsumer(
            consumer_group=self.__consume_strategy.get_subscription_group(subscriber),
            group_instance_id=self.__generate_consumer_group_instance_id(subscriber),
            topics=topics,
            connection_config=self.__connection_config,
            initial_offset_position=self.__consumer_initial_offset_position,
            partition_assignors=self.__kafka_partition_assignors + self.__FALLBACK_PARTITION_ASSIGNORS,
            logger=self._logger,
            kafka_admin_client=self.__kafka_admin_client,
            auto_create_topic_configuration=self.__auto_create_topic_configuration,
            on_partition_assigned=self.__on_partition_assigned,
            on_partition_revoked=self.__on_partition_revoked,
            session_timeout_ms=self.__session_timeout_ms,
            max_poll_interval_ms=self.__max_poll_interval_ms,
            heartbeat_interval_ms=self.__heartbeat_interval_ms,
            wait_for_connection_to_cluster_ms=self.__wait_for_connection_to_cluster_ms,
        )

        self.__executor_per_consumer_mapper[kafka_consumer] = executor

        self.__queue_per_consumer_mapper[kafka_consumer] = InMemoryMultiqueueRepository()

        self._logger.info(
            f"Initializing consumer group: '{kafka_consumer.get_consumer_group()}' subscribed to the topics: '{kafka_consumer.get_topics()}'"
        )

        await kafka_consumer.init()

        self._logger.info(
            f"Initialized consumer group: '{kafka_consumer.get_consumer_group()}' subscribed to the topics: '{kafka_consumer.get_topics()}'"
        )

    def __generate_consumer_group_instance_id(self, subscriber: MetaSubscriber) -> Optional[str]:
        if self.__worker_instance_id is None:
            return None
        return f"{subscriber.fqn()}-{self.__worker_instance_id}"

    @abstractmethod
    async def _create_kafka_consumer_executor(self, subscriber: MetaSubscriber) -> KafkaEventSubscriberExecutor:
        pass

    async def __polling_task(self) -> None:
        self._logger.info("Creating polling tasks")
        try:
            polling_task_per_consumer = [
                create_task(self.__polling_consuming_tasks(consumer))
                for consumer, subscriber in self.__queue_per_consumer_mapper.items()
            ]

            await gather(*polling_task_per_consumer)

        except Exception:
            self._logger.error(f"Polling task failed with exception: {traceback.format_exc()}")
            self.__should_stop.set()

    async def __polling_consuming_tasks(self, consumer: AIOKafkaConsumer) -> None:
        queue = self.__queue_per_consumer_mapper[consumer]
        while not self.__should_stop.is_set():
            total_size = sum([queue.get_total_size() for queue in self.__queue_per_consumer_mapper.values()])
            if total_size >= self.__max_queue_size:
                await sleep(self.__seconds_between_polls_if_there_are_tasks_in_the_queue)
                continue

            async with self.__polling_tasks_semaphore:
                kafka_poll_records = await consumer.poll(
                    number_of_messages_to_poll=self.__max_records_retrieved_per_poll,
                )

                for kafka_poll_record in kafka_poll_records:
                    queue.push(
                        key=TopicPartition(
                            topic=kafka_poll_record.topic,
                            partition=kafka_poll_record.partition,
                        ),
                        record=kafka_poll_record,
                    )

            if len(kafka_poll_records) == 0:
                await sleep(self.__seconds_between_polls_if_there_are_no_new_tasks)

    async def __consume_events_task(self) -> None:
        self._logger.info("Creating consuming task")
        blocked_tasks_iterator = self.__generate_blocked_consuming_tasks_iterator()

        async for consuming_task in blocked_tasks_iterator:
            consumer = consuming_task.consumer
            kafka_poll_record = consuming_task.kafka_poll_record

            executor = self.__executor_per_consumer_mapper[consumer]
            await executor.consume(kafka_poll_record=kafka_poll_record)
            await consumer.commit_poll_record(kafka_poll_record)

            self.__events_processed += 1

    # This iterator return a blocked task, that will be blocked for other process (like rebalancing), until the next task will be requested
    async def __generate_blocked_consuming_tasks_iterator(self) -> AsyncIterator[ConsumingTask]:
        consumer_queues_cyclic_iterator = cycle(self.__queue_per_consumer_mapper.items())
        last_consumer, _ = next(consumer_queues_cyclic_iterator)

        while not self.__should_stop.is_set():
            if self.is_rebalancing_in_progress():
                self._logger.info("Waiting for rebalancing")
                await sleep(self.__SECONDS_TO_WAIT_BETWEEN_REBALANCING_IN_PROGRESS)
                continue

            if await self.__all_queues_are_empty():
                await sleep(self.__seconds_between_executions_if_there_are_no_tasks_in_the_queue)
                continue

            consumer: Optional[AIOKafkaConsumer] = None

            while consumer != last_consumer:
                consumer, queue = next(consumer_queues_cyclic_iterator)
                async with self.__get_consumer_mutex(
                    consumer_fqn=consumer.get_consumer_group(),
                ):
                    kafka_poll_record = queue.pop()

                    if kafka_poll_record is not None:
                        yield ConsumingTask(consumer, kafka_poll_record)

                    last_consumer = consumer
                    break

    def __get_consumer_mutex(self, consumer_fqn: str) -> Lock:
        mutex_key = f"consumer_{consumer_fqn}"
        return self.__consumer_and_partition_mutex[mutex_key]

    async def __all_queues_are_empty(self) -> bool:
        return all([queue.is_totally_empty() for queue in self.__queue_per_consumer_mapper.values()])

    async def __on_partition_assigned(self, consumer: AIOKafkaConsumer, topics_partitions: set[TopicPartition]) -> None:
        self._logger.info(
            f"rebalancing in progress, assigning partitions {topics_partitions} to consumer {consumer.get_consumer_group()}"
        )
        for topic_partition in topics_partitions:
            self.__queue_per_consumer_mapper[consumer].create_key(topic_partition)

    async def __on_partition_revoked(self, consumer: AIOKafkaConsumer, topics_partitions: set[TopicPartition]) -> None:
        self._logger.info(
            f"rebalancing in progress, revoking partitions {topics_partitions} from consumer {consumer.get_consumer_group()}"
        )

        self.increase_number_of_rebalancing_in_progress()
        async with self.__get_consumer_mutex(
            consumer_fqn=consumer.get_consumer_group(),
        ):
            for topic_partition in topics_partitions:
                self.__queue_per_consumer_mapper[consumer].remove_key(topic_partition)

        self.decrease_number_of_rebalancing_in_progress()

    def increase_number_of_rebalancing_in_progress(self) -> None:
        self.__number_of_rebalancing_processes_in_progress += 1

    def decrease_number_of_rebalancing_in_progress(self) -> None:
        self.__number_of_rebalancing_processes_in_progress -= 1

    def is_rebalancing_in_progress(self) -> bool:
        return self.__number_of_rebalancing_processes_in_progress > 0

    def request_stop(self) -> None:
        self.__should_stop.set()
        self._logger.info("Worker stop requested. Waiting for finalize the current task")

    async def __manage_kafka_consumers_stopping(self) -> None:
        await gather(*[kafka_consumer.stop() for kafka_consumer in self.__queue_per_consumer_mapper.keys()])

    async def __health_check(self, request: web.Request) -> web.Response:
        health_information = {
            "subscribers": [subscriber.fqn() for subscriber in self.__subscribers],
            "number_of_subscribers": len(self.__subscribers),
            "event_processed": self.__events_processed,
        }

        return web.Response(text=json.dumps(health_information), content_type="application/json")

    async def __is_ready(self, request: web.Request) -> web.Response:
        is_ready = self.__is_worked_initialized
        status_code = 200 if is_ready else 503

        self._logger.info(f"Health check is_ready: {is_ready}, status_code: {status_code}")

        return web.Response(
            text=json.dumps({"is_ready": is_ready}), content_type="application/json", status=status_code
        )

    def __print_statistics(self) -> None:
        self._logger.info(
            f"System startup summary:\n"
            f"  - Number of subscribers: {len(self.__subscribers)}\n"
            f"  - Start Kafka consumers elapsed time: {self.__start_kafka_consumers_elapsed_time}\n"
            f"  - Initial coroutines created elapsed time: {self.__initial_coroutines_created_elapsed_time}\n"
            f"  - Events processed: {self.__events_processed}\n"
            f"  - Events processed elapsed time: {self.__events_processed_elapsed_time}"
        )
