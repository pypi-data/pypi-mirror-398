from __future__ import annotations

import asyncio
from logging import Logger
from typing import Awaitable, Callable, Optional, Sequence, cast

from aiokafka import AIOKafkaConsumer as AIOKafkaNativeConsumer, ConsumerRecord, TopicPartition, OffsetAndMetadata
from aiokafka.helpers import create_ssl_context

from buz.event.infrastructure.buz_kafka.exceptions.kafka_event_bus_config_not_valid_exception import (
    KafkaEventBusConfigNotValidException,
)
from buz.kafka.domain.exceptions.topic_already_created_exception import KafkaTopicsAlreadyCreatedException
from buz.kafka.domain.models.auto_create_topic_configuration import AutoCreateTopicConfiguration
from buz.kafka.domain.models.consumer_initial_offset_position import ConsumerInitialOffsetPosition
from buz.kafka.domain.models.create_kafka_topic import CreateKafkaTopic
from buz.kafka.domain.models.kafka_connection_config import KafkaConnectionConfig
from buz.kafka.domain.models.kafka_poll_record import KafkaPollRecord
from buz.kafka.domain.models.kafka_supported_security_protocols import KafkaSupportedSecurityProtocols
from buz.kafka.domain.services.kafka_admin_client import KafkaAdminClient
from buz.kafka.infrastructure.aiokafka.rebalance.kafka_callback_rebalancer import KafkaCallbackRebalancer
from buz.kafka.infrastructure.aiokafka.translators.consumer_initial_offset_position_translator import (
    AIOKafkaConsumerInitialOffsetPositionTranslator,
)


class AIOKafkaConsumer:
    __DEFAULT_POLL_TIMEOUT_MS = 0
    __DEFAULT_ASYNC_FUNCTION_TIMEOUT_MS = 3000

    def __init__(
        self,
        *,
        consumer_group: str,
        topics: list[str],
        connection_config: KafkaConnectionConfig,
        kafka_admin_client: Optional[KafkaAdminClient],
        initial_offset_position: ConsumerInitialOffsetPosition,
        partition_assignors: tuple,
        logger: Logger,
        session_timeout_ms: int,
        max_poll_interval_ms: int,
        heartbeat_interval_ms: int,
        on_partition_revoked: Callable[[AIOKafkaConsumer, set[TopicPartition]], Awaitable[None]],
        on_partition_assigned: Callable[[AIOKafkaConsumer, set[TopicPartition]], Awaitable[None]],
        auto_create_topic_configuration: Optional[AutoCreateTopicConfiguration] = None,
        wait_for_connection_to_cluster_ms: Optional[int] = None,
        group_instance_id: Optional[str] = None,
    ) -> None:
        self.__consumer_group = consumer_group
        self.__topics = topics
        self.__initial_offset_position = initial_offset_position
        self.__connection_config = connection_config
        self.__kafka_admin_client = kafka_admin_client
        self.__partition_assignors = partition_assignors
        self.__logger = logger
        self.__session_timeout_ms = session_timeout_ms
        self.__auto_create_topic_configuration = auto_create_topic_configuration
        self.__on_partitions_revoked_callback = on_partition_revoked
        self.__on_partitions_assigned_callback = on_partition_assigned
        self.__max_poll_interval_ms = max_poll_interval_ms
        self.__heartbeat_interval_ms = heartbeat_interval_ms
        self.__wait_for_connection_to_cluster_ms = wait_for_connection_to_cluster_ms
        self.__group_instance_id = group_instance_id
        self.__check_kafka_admin_client_is_needed()
        self.__consumer = self.__generate_consumer()

    def get_topics(self) -> Sequence[str]:
        return list(self.__topics)

    def get_consumer_group(self) -> str:
        return self.__consumer_group

    def __check_kafka_admin_client_is_needed(self) -> None:
        if self.__kafka_admin_client is None and self.__auto_create_topic_configuration is not None:
            raise KafkaEventBusConfigNotValidException(
                "A KafkaAdminClient is needed to create topics when 'auto_create_topic_configuration' is set."
            )

    def __generate_consumer(self) -> AIOKafkaNativeConsumer:
        if self.__auto_create_topic_configuration is not None:
            self.__ensure_topics_are_created(self.__auto_create_topic_configuration)

        sasl_mechanism = (
            self.__connection_config.credentials.sasl_mechanism.value
            if self.__connection_config.credentials.sasl_mechanism
            else "PLAIN"
        )

        ssl_context = (
            create_ssl_context()
            if self.__connection_config.credentials.security_protocol == KafkaSupportedSecurityProtocols.SASL_SSL
            else None
        )

        consumer = AIOKafkaNativeConsumer(
            None,
            group_instance_id=self.__group_instance_id,
            ssl_context=ssl_context,
            bootstrap_servers=",".join(self.__connection_config.bootstrap_servers),
            security_protocol=self.__connection_config.credentials.security_protocol.value,
            sasl_mechanism=sasl_mechanism,
            sasl_plain_username=self.__connection_config.credentials.user,
            sasl_plain_password=self.__connection_config.credentials.password,
            client_id=self.__connection_config.client_id,
            group_id=self.__consumer_group,
            enable_auto_commit=False,
            auto_offset_reset=AIOKafkaConsumerInitialOffsetPositionTranslator.to_kafka_supported_format(
                self.__initial_offset_position
            ),
            session_timeout_ms=self.__session_timeout_ms,
            heartbeat_interval_ms=self.__heartbeat_interval_ms,
            # partition_assignment_strategy=list(self.__partition_assignors),
            max_poll_interval_ms=self.__max_poll_interval_ms,
            rebalance_timeout_ms=self.__max_poll_interval_ms,
        )

        return consumer

    def __ensure_topics_are_created(self, auto_create_topic_configuration: AutoCreateTopicConfiguration) -> None:
        kafka_admin_client = self.__get_kafka_admin_client()
        non_created_topics = [topic for topic in self.__topics if not kafka_admin_client.is_topic_created(topic)]

        if len(non_created_topics) == 0:
            return None

        topics_to_create = [
            CreateKafkaTopic(
                name=topic,
                partitions=auto_create_topic_configuration.partitions,
                replication_factor=auto_create_topic_configuration.replication_factor,
                configs=auto_create_topic_configuration.configs,
            )
            for topic in non_created_topics
        ]

        try:
            self.__logger.info(f"Creating missing topics: {non_created_topics}...")
            kafka_admin_client.create_topics(topics=topics_to_create)
            self.__logger.info(f"Created missing topics: {non_created_topics}")
        except KafkaTopicsAlreadyCreatedException:
            # there is a possibility to have a race condition between the check and the creation
            # but it does not matters, the important part is that the topic is created
            pass

    def __get_kafka_admin_client(self) -> KafkaAdminClient:
        if self.__kafka_admin_client is None:
            raise KafkaEventBusConfigNotValidException("KafkaAdminClient is not set.")
        return self.__kafka_admin_client

    async def init(self) -> None:
        self.__consumer.subscribe(
            topics=self.__topics,
            listener=KafkaCallbackRebalancer(
                logger=self.__logger,
                on_partitions_assigned=self.__on_partitions_assigned,
                on_partitions_revoked=self.__on_partitions_revoked,
            ),
        )

        self.__logger.info(f"Initializing connection of consumer with group_id={self.__consumer_group}")

        if self.__wait_for_connection_to_cluster_ms is not None:
            await asyncio.wait_for(self.__consumer.start(), self.__wait_for_connection_to_cluster_ms / 1000)
        else:
            await self.__consumer.start()

    async def __on_partitions_assigned(
        self,
        topics_partitions: set[TopicPartition],
    ) -> None:
        await self.__on_partitions_assigned_callback(self, topics_partitions)

    async def __on_partitions_revoked(
        self,
        topics_partitions: set[TopicPartition],
    ) -> None:
        await self.__on_partitions_revoked_callback(self, topics_partitions)

    async def poll(
        self,
        *,
        number_of_messages_to_poll: Optional[int] = None,
    ) -> list[KafkaPollRecord]:
        poll_results = await self.__get_many(
            max_records=number_of_messages_to_poll,
        )

        if poll_results is None:
            return []

        results = [
            cast(KafkaPollRecord, consumer_record)
            for consumer_records in poll_results.values()
            for consumer_record in consumer_records
        ]

        return results

    async def __get_many(
        self,
        max_records: Optional[int] = None,
    ) -> Optional[dict[TopicPartition, list[ConsumerRecord]]]:
        try:
            return await asyncio.wait_for(
                self.__consumer.getmany(timeout_ms=self.__DEFAULT_POLL_TIMEOUT_MS, max_records=max_records),
                timeout=self.__DEFAULT_ASYNC_FUNCTION_TIMEOUT_MS / 1000,
            )
        except asyncio.TimeoutError:
            self.__logger.debug("Timeout while polling")
            return None

    async def commit_poll_record(self, poll_record: KafkaPollRecord) -> None:
        topic_partition = TopicPartition(topic=poll_record.topic, partition=poll_record.partition)
        offset = {topic_partition: OffsetAndMetadata(poll_record.offset + 1, "")}

        await self.__consumer.commit(offset)

    async def stop(self) -> None:
        self.__logger.info(f"Closing connection of consumer with group_id={self.__consumer_group}")

        self.__consumer.unsubscribe()

        try:
            await asyncio.wait_for(
                self.__consumer.stop(),
                timeout=self.__DEFAULT_ASYNC_FUNCTION_TIMEOUT_MS / 1000,
            )
        except asyncio.TimeoutError:
            self.__logger.debug("Timeout while stopping consumer")
