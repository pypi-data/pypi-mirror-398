from logging import Logger
from typing import Optional, Sequence, Type, TypeVar

from aiokafka.coordinator.assignors.abstract import AbstractPartitionAssignor
from buz.kafka.infrastructure.deserializers.implementations.cdc.cdc_record_bytes_to_cdc_payload_deserializer import (
    CDCRecordBytesToCDCPayloadDeserializer,
)
from buz.kafka.infrastructure.deserializers.implementations.cdc.cdc_record_bytes_to_event_deserializer import (
    CDCRecordBytesToEventDeserializer,
)

from buz.event import Event
from buz.event.async_subscriber import AsyncSubscriber
from buz.event.infrastructure.buz_kafka.base_buz_aiokafka_async_consumer import BaseBuzAIOKafkaAsyncConsumer
from buz.event.infrastructure.buz_kafka.consume_strategy.consume_strategy import KafkaConsumeStrategy
from buz.event.infrastructure.buz_kafka.consume_strategy.kafka_on_fail_strategy import KafkaOnFailStrategy
from buz.event.infrastructure.buz_kafka.kafka_event_async_subscriber_executor import KafkaEventAsyncSubscriberExecutor
from buz.event.infrastructure.buz_kafka.kafka_event_subscriber_executor import KafkaEventSubscriberExecutor
from buz.event.meta_subscriber import MetaSubscriber
from buz.event.middleware.async_consume_middleware import AsyncConsumeMiddleware
from buz.event.strategies.retry.consume_retrier import ConsumeRetrier
from buz.event.strategies.retry.reject_callback import RejectCallback
from buz.kafka.domain.models.auto_create_topic_configuration import AutoCreateTopicConfiguration
from buz.kafka.domain.models.consumer_initial_offset_position import ConsumerInitialOffsetPosition
from buz.kafka.domain.models.kafka_connection_config import KafkaConnectionConfig
from buz.kafka.domain.services.kafka_admin_client import KafkaAdminClient
from buz.kafka.infrastructure.deserializers.byte_deserializer import ByteDeserializer
from buz.kafka.infrastructure.deserializers.bytes_to_message_deserializer import BytesToMessageDeserializer
from buz.kafka.infrastructure.deserializers.implementations.json_bytes_to_message_deserializer import (
    JSONBytesToMessageDeserializer,
)
from buz.kafka.infrastructure.serializers.kafka_header_serializer import KafkaHeaderSerializer

T = TypeVar("T", bound=Event)


class BuzAIOKafkaAsyncConsumer(BaseBuzAIOKafkaAsyncConsumer):
    def __init__(
        self,
        *,
        connection_config: KafkaConnectionConfig,
        kafka_admin_client: Optional[KafkaAdminClient],
        consume_strategy: KafkaConsumeStrategy,
        on_fail_strategy: KafkaOnFailStrategy,
        max_queue_size: int,
        max_records_retrieved_per_poll: int,
        kafka_partition_assignors: tuple[Type[AbstractPartitionAssignor], ...] = (),
        subscribers: Sequence[AsyncSubscriber],
        logger: Logger,
        consumer_initial_offset_position: ConsumerInitialOffsetPosition,
        deserializers_per_subscriber: dict[MetaSubscriber, BytesToMessageDeserializer[T]],
        worker_instance_id: Optional[str] = None,
        consume_middlewares: Optional[Sequence[AsyncConsumeMiddleware]] = None,
        consume_retrier: Optional[ConsumeRetrier] = None,
        reject_callback: Optional[RejectCallback] = None,
        auto_create_topic_configuration: Optional[AutoCreateTopicConfiguration] = None,
        seconds_between_executions_if_there_are_no_tasks_in_the_queue: Optional[int] = None,
        seconds_between_polls_if_there_are_tasks_in_the_queue: Optional[int] = None,
        seconds_between_polls_if_there_are_no_new_tasks: Optional[int] = None,
        max_number_of_concurrent_polling_tasks: Optional[int] = None,
        session_timeout_ms: Optional[int] = None,
        max_poll_interval_ms: Optional[int] = None,
        heartbeat_interval_ms: Optional[int] = None,
        health_check_port: Optional[int] = None,
        wait_for_connection_to_cluster_ms: Optional[int] = None,
        milliseconds_between_retries: int = 5000,
    ):
        super().__init__(
            connection_config=connection_config,
            kafka_admin_client=kafka_admin_client,
            consume_strategy=consume_strategy,
            max_queue_size=max_queue_size,
            max_records_retrieved_per_poll=max_records_retrieved_per_poll,
            kafka_partition_assignors=kafka_partition_assignors,
            subscribers=subscribers,
            logger=logger,
            consumer_initial_offset_position=consumer_initial_offset_position,
            auto_create_topic_configuration=auto_create_topic_configuration,
            seconds_between_executions_if_there_are_no_tasks_in_the_queue=seconds_between_executions_if_there_are_no_tasks_in_the_queue,
            seconds_between_polls_if_there_are_tasks_in_the_queue=seconds_between_polls_if_there_are_tasks_in_the_queue,
            seconds_between_polls_if_there_are_no_new_tasks=seconds_between_polls_if_there_are_no_new_tasks,
            max_number_of_concurrent_polling_tasks=max_number_of_concurrent_polling_tasks,
            session_timeout_ms=session_timeout_ms,
            max_poll_interval_ms=max_poll_interval_ms,
            heartbeat_interval_ms=heartbeat_interval_ms,
            health_check_port=health_check_port,
            wait_for_connection_to_cluster_ms=wait_for_connection_to_cluster_ms,
            worker_instance_id=worker_instance_id,
            milliseconds_between_retries=milliseconds_between_retries,
        )
        self.__on_fail_strategy = on_fail_strategy
        self.__consume_middlewares = consume_middlewares
        self.__consume_retrier = consume_retrier
        self.__reject_callback = reject_callback
        self._deserializers_per_subscriber = deserializers_per_subscriber
        self.__milliseconds_between_retries = milliseconds_between_retries

    async def _create_kafka_consumer_executor(
        self,
        subscriber: MetaSubscriber,
    ) -> KafkaEventSubscriberExecutor:
        if not isinstance(subscriber, AsyncSubscriber):
            raise TypeError(
                f"Subscriber {subscriber.__class__.__name__} is not a subclass of Subscriber, probably you are trying to use a synchronous subscriber"
            )

        byte_deserializer: ByteDeserializer[Event] = self._deserializers_per_subscriber.get(
            subscriber
        ) or JSONBytesToMessageDeserializer(
            # todo: it looks like in next python versions the inference engine is powerful enough to ensure this type, so we can remove it when we upgrade the python version of the library
            event_class=subscriber.handles()  # type: ignore
        )

        cdc_payload_deserializer = (
            CDCRecordBytesToCDCPayloadDeserializer()
            if isinstance(byte_deserializer, CDCRecordBytesToEventDeserializer)
            else None
        )

        return KafkaEventAsyncSubscriberExecutor(
            subscriber=subscriber,
            logger=self._logger,
            consume_middlewares=self.__consume_middlewares,
            milliseconds_between_retries=self.__milliseconds_between_retries,
            byte_deserializer=byte_deserializer,
            header_deserializer=KafkaHeaderSerializer(),
            on_fail_strategy=self.__on_fail_strategy,
            consume_retrier=self.__consume_retrier,
            reject_callback=self.__reject_callback,
            cdc_payload_deserializer=cdc_payload_deserializer,
        )
