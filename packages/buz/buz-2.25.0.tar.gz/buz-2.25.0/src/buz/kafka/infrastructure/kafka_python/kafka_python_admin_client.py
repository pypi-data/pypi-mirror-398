from __future__ import annotations

from datetime import datetime
from logging import Logger
import re
from typing import Any, Callable, Optional, Sequence, cast

from cachetools import TTLCache
from kafka import KafkaClient, KafkaConsumer
from kafka.admin import KafkaAdminClient as KafkaPythonLibraryAdminClient, NewTopic
from kafka.admin.new_partitions import NewPartitions
from kafka.errors import TopicAlreadyExistsError
from kafka.structs import TopicPartition, OffsetAndTimestamp

from buz.kafka.domain.exceptions.consumer_group_not_found_exception import ConsumerGroupNotFoundException
from buz.kafka.domain.exceptions.not_all_partition_assigned_exception import NotAllPartitionAssignedException
from buz.kafka.domain.exceptions.not_valid_partition_number_exception import NotValidPartitionNumberException
from buz.kafka.domain.exceptions.topic_already_created_exception import KafkaTopicsAlreadyCreatedException
from buz.kafka.domain.exceptions.topic_not_found_exception import TopicNotFoundException
from buz.kafka.domain.models.consumer_initial_offset_position import ConsumerInitialOffsetPosition
from buz.kafka.domain.models.create_kafka_topic import CreateKafkaTopic
from buz.kafka.domain.models.kafka_connection_config import KafkaConnectionConfig
from buz.kafka.domain.services.kafka_admin_client import KafkaAdminClient

from buz.kafka.infrastructure.kafka_python.translators.consumer_initial_offset_position_translator import (
    KafkaPythonConsumerInitialOffsetPositionTranslator,
)

INTERNAL_KAFKA_TOPICS = {"__consumer_offsets", "_schema"}
TOPIC_CACHE_KEY = "topics"


class KafkaPythonAdminClient(KafkaAdminClient):
    __PYTHON_KAFKA_DUPLICATED_TOPIC_ERROR_CODE = 36

    _kafka_admin: Optional[KafkaPythonLibraryAdminClient] = None
    _kafka_client: Optional[KafkaClient] = None

    def __init__(
        self,
        *,
        logger: Logger,
        connection_config: KafkaConnectionConfig,
        cache_ttl_seconds: int = 0,
    ):
        self._logger = logger
        self.__connection_config = connection_config
        self._config_in_library_format = self.__get_kafka_config_in_library_format(self.__connection_config)
        self.__ttl_cache: TTLCache[str, Any] = TTLCache(maxsize=1, ttl=cache_ttl_seconds)

    def __get_kafka_config_in_library_format(self, config: KafkaConnectionConfig) -> dict:
        return {
            "client_id": config.client_id,
            "bootstrap_servers": config.bootstrap_servers,
            "security_protocol": config.credentials.security_protocol.value,
            "sasl_mechanism": config.credentials.sasl_mechanism.value if config.credentials.sasl_mechanism else None,
            "sasl_plain_username": config.credentials.user,
            "sasl_plain_password": config.credentials.password,
        }

    def connect(self):
        self._get_kafka_admin()
        self._get_kafka_client()

    def disconnect(self):
        if self._kafka_admin is not None:
            self._kafka_admin.close()
            self._kafka_admin = None
        if self._kafka_client is not None:
            self._kafka_client.close()
            self._kafka_client = None

    def _get_kafka_admin(self) -> KafkaPythonLibraryAdminClient:
        if not self._kafka_admin:
            self._kafka_admin = KafkaPythonLibraryAdminClient(**self._config_in_library_format)
        return self._kafka_admin

    def _get_kafka_client(self) -> KafkaClient:
        if not self._kafka_client:
            self._kafka_client = KafkaClient(**self._config_in_library_format)
        return self._kafka_client

    def create_topics(
        self,
        *,
        topics: Sequence[CreateKafkaTopic],
    ) -> None:
        new_topics = [
            NewTopic(
                name=topic.name,
                num_partitions=topic.partitions,
                replication_factor=topic.replication_factor,
                topic_configs=topic.configs,
            )
            for topic in topics
        ]

        try:
            self._get_kafka_admin().create_topics(new_topics=new_topics)
        except TopicAlreadyExistsError as error:
            topic_names = self.__get_list_of_kafka_topics_from_topic_already_exists_error(error)
            raise KafkaTopicsAlreadyCreatedException(topic_names=topic_names)

    def __get_list_of_kafka_topics_from_topic_already_exists_error(self, error: TopicAlreadyExistsError) -> list[str]:
        message = str(error)
        response_message = re.search(r"topic_errors=\[.*?]", message)
        topic_messages = re.findall(
            r"topic='[^']*', error_code=" + str(self.__PYTHON_KAFKA_DUPLICATED_TOPIC_ERROR_CODE), response_message[0]  # type: ignore
        )

        return [re.search("'.*'", topic_message)[0].strip("'") for topic_message in topic_messages]  # type: ignore

    def is_topic_created(
        self,
        topic: str,
    ) -> bool:
        return topic in self.get_topics()

    def get_topics(
        self,
    ) -> set[str]:
        return self.__resolve_cached_property(
            TOPIC_CACHE_KEY, lambda: set(self._get_kafka_admin().list_topics()) - INTERNAL_KAFKA_TOPICS
        )

    def __resolve_cached_property(self, property_key: str, callback: Callable) -> Any:
        value = self.__ttl_cache.get(property_key)
        if value is not None:
            return value
        value = callback()
        self.__ttl_cache[property_key] = value
        return value

    def delete_topics(
        self,
        *,
        topics: set[str],
    ) -> None:
        self._get_kafka_admin().delete_topics(
            topics=topics,
        )
        self.__remove_cache_property(TOPIC_CACHE_KEY)

    def __remove_cache_property(self, property_key: str) -> None:
        self.__ttl_cache.pop(property_key, None)

    def delete_subscription_groups(
        self,
        *,
        subscription_groups: set[str],
    ) -> list[tuple[str, Any]]:
        results = self._get_kafka_admin().delete_consumer_groups(group_ids=subscription_groups)
        return results

    def get_cluster_consumer_groups(
        self,
    ) -> set[str]:
        return set([consumer_group_tuple[0] for consumer_group_tuple in self._get_kafka_admin().list_consumer_groups()])

    def _wait_for_cluster_update(self) -> None:
        future = self._get_kafka_client().cluster.request_update()
        self._get_kafka_client().poll(future=future)

    def move_offsets_to_datetime(
        self,
        *,
        consumer_group: str,
        topic: str,
        target_datetime: datetime,
    ) -> None:
        (consumer, topic_partitions) = self.__get_consumer_with_all_partitions_assigned(
            consumer_group=consumer_group,
            topic=topic,
        )

        offsets_for_date = self.__get_first_offset_after_date(
            consumer=consumer,
            topic_partitions=topic_partitions,
            target_datetime=target_datetime,
        )

        try:
            end_offsets = consumer.end_offsets(topic_partitions)

            if end_offsets is None or len(end_offsets.keys()) != len(topic_partitions):
                raise Exception(f'There was an error extracting the end offsets of the topic "{topic}"')

            for topic_partition in topic_partitions:
                offset_and_timestamp = offsets_for_date.get(topic_partition)
                if offset_and_timestamp:
                    self._logger.info(f'moving "{topic_partition}" to the offset "{offset_and_timestamp.offset}"')
                    consumer.seek(topic_partition, offset_and_timestamp.offset)
                else:
                    self._logger.info(
                        f'moving "{topic_partition}" to the end of the topic because there are no messages later than "{target_datetime}"'
                    )
                    consumer.seek(topic_partition, end_offsets[topic_partition])

            consumer.commit()
        except Exception as exception:
            consumer.close()
            raise exception

        consumer.close()

    def __get_consumer_with_all_partitions_assigned(
        self,
        consumer_group: str,
        topic: str,
    ) -> tuple[KafkaConsumer, Sequence[TopicPartition]]:
        consumer = KafkaConsumer(
            group_id=consumer_group,
            enable_auto_commit=False,
            auto_offset_reset=KafkaPythonConsumerInitialOffsetPositionTranslator.to_kafka_supported_format(
                ConsumerInitialOffsetPosition.BEGINNING
            ),
            **self._config_in_library_format,
        )

        try:
            partitions = self.get_number_of_partitions(topic)

            topic_partitions = [TopicPartition(topic=topic, partition=partition) for partition in range(partitions)]

            consumer.subscribe(topic)

            self.__force_partition_assignment(consumer)

            # We need all the partitions in order to update the offsets
            if len(consumer.assignment()) != len(topic_partitions):
                raise NotAllPartitionAssignedException(
                    topic_name=topic,
                    consumer_group=consumer_group,
                )

            # This could produce a race condition, but it is a limitation of kafka admin (we are not able to check if all the partition are assigned using the manual assignment)
            # https://github.com/dpkp/kafka-python/blob/master/kafka/consumer/group.py#L430
            consumer.unsubscribe()
            consumer.assign(topic_partitions)
            self.__force_partition_assignment(consumer)

            return (consumer, topic_partitions)
        except Exception as exception:
            consumer.close()
            raise exception

    def __get_first_offset_after_date(
        self,
        *,
        consumer: KafkaConsumer,
        topic_partitions: Sequence[TopicPartition],
        target_datetime: datetime,
    ) -> dict[TopicPartition, Optional[OffsetAndTimestamp]]:
        offset_for_times: dict[TopicPartition, Optional[int]] = {}
        timestamp_ms = int(target_datetime.timestamp() * 1000)

        for topic_partition in topic_partitions:
            offset_for_times[topic_partition] = timestamp_ms

        return cast(
            dict[TopicPartition, Optional[OffsetAndTimestamp]],
            consumer.offsets_for_times(offset_for_times),
        )

    # We are not to commit the new offset, but we need to execute a polling in order to start the partition assignment
    def __force_partition_assignment(self, consumer: KafkaConsumer) -> None:
        consumer.poll(max_records=1, timeout_ms=0)

    def increase_topic_partitions_and_set_offset_of_related_consumer_groups_to_the_beginning_of_the_new_ones(
        self,
        *,
        topic: str,
        new_number_of_partitions: int,
        consumer_groups_to_ignore: Optional[set[str]] = None,
    ) -> None:
        self._logger.info(
            f'Increasing topic "{topic}" partitions: Verifying the new number of partitions "{new_number_of_partitions}"'
        )

        previous_partitions_number = self.get_number_of_partitions(topic)
        topic_partitions = [
            TopicPartition(topic=topic, partition=partition) for partition in range(previous_partitions_number)
        ]

        if previous_partitions_number >= new_number_of_partitions:
            raise NotValidPartitionNumberException(
                partition_number=new_number_of_partitions,
                min_partition_number=len(topic_partitions),
            )

        self._logger.info(f'Increasing topic "{topic}" partitions: Extracting related consumer groups')
        related_consumer_groups = self.__get_consumer_groups_related_to_a_topic(topic_partitions)

        if consumer_groups_to_ignore:
            consumer_groups_to_ignore_set = set[str](consumer_groups_to_ignore)
            related_consumer_groups = related_consumer_groups - consumer_groups_to_ignore_set

        self._logger.info(
            f'Increasing topic "{topic}" partitions: The following consumer groups will be updated:"{related_consumer_groups}"'
        )

        consumers_to_update: list[KafkaConsumer] = []
        new_partitions_consumer: Optional[KafkaConsumer] = None

        try:
            for consumer_group in related_consumer_groups:
                self._logger.info(
                    f'Increasing topic "{topic}" partitions: Requesting the assignment of the partitions of the group "{consumer_group}"'
                )
                (consumer_with_all_partitions, _) = self.__get_consumer_with_all_partitions_assigned(
                    consumer_group=consumer_group,
                    topic=topic,
                )
                consumers_to_update.append(consumer_with_all_partitions)

            self._logger.info(
                f'Increasing topic "{topic}" partitions: Incrementing the partition to "{new_number_of_partitions}"'
            )

            self._get_kafka_admin().create_partitions(
                {
                    topic: NewPartitions(total_count=new_number_of_partitions),
                }
            )

            new_partitions = [
                TopicPartition(
                    topic=topic,
                    partition=partition_index,
                )
                for partition_index in range(previous_partitions_number, new_number_of_partitions)
            ]

            for consumer_group in related_consumer_groups:
                self._logger.info(
                    f'Increasing topic "{topic}" partitions: Moving the offset of the consumer group "{consumer_group}" to the beginning of the new partitions'
                )
                # We need to create a new consumer because kafka-python has a limitation that does not allow to assign specific partitions to a consumer subscribed to an entire topic
                new_partitions_consumer = KafkaConsumer(
                    group_id=consumer_group,
                    enable_auto_commit=False,
                    auto_offset_reset=KafkaPythonConsumerInitialOffsetPositionTranslator.to_kafka_supported_format(
                        ConsumerInitialOffsetPosition.BEGINNING
                    ),
                    **self._config_in_library_format,
                )
                new_partitions_consumer.assign(new_partitions)
                for new_partition in new_partitions:
                    new_partitions_consumer.seek(new_partition, 0)
                new_partitions_consumer.commit()
                new_partitions_consumer.close()

            self._logger.info(f'Increasing topic "{topic}" partitions: Process complete')

        except Exception as exception:
            for consumer_with_all_partitions in consumers_to_update:
                consumer_with_all_partitions.close()

            if new_partitions_consumer is not None:
                new_partitions_consumer.close()

            self._logger.error(f'Increasing topic "{topic}" partitions: unexpected error {exception}')
            raise exception

        return

    def get_number_of_partitions(self, topic: str) -> int:
        consumer = KafkaConsumer(
            enable_auto_commit=False,
            auto_offset_reset=KafkaPythonConsumerInitialOffsetPositionTranslator.to_kafka_supported_format(
                ConsumerInitialOffsetPosition.BEGINNING
            ),
            **self._config_in_library_format,
        )

        try:
            partitions = consumer.partitions_for_topic(topic)
            if partitions is None:
                raise TopicNotFoundException(topic_name=topic)

            return len(partitions)
        except Exception as exception:
            consumer.close()
            raise exception

    # The purpose of this function is to get all the consumer groups that are consuming from the topic
    # It is a heavy tasks because we need to get the offset of all the partitions of the topic
    def __get_consumer_groups_related_to_a_topic(self, topic_partitions: Sequence[TopicPartition]) -> set[str]:
        cluster_consumer_groups = self.get_cluster_consumer_groups()

        related_consumer_groups: set[str] = set()

        for consumer_group in cluster_consumer_groups:
            partitions_offsets = list(
                self._get_kafka_admin()
                .list_consumer_group_offsets(consumer_group, partitions=topic_partitions)
                .values()
            )

            partitions_with_valid_offsets = [partition for partition in partitions_offsets if partition.offset != -1]

            if len(partitions_with_valid_offsets) == 0:
                continue

            related_consumer_groups.add(consumer_group)

        return related_consumer_groups

    def get_consumer_group_offsets(self, *, consumer_group: str, topic: str) -> dict[int, int]:
        self._logger.info(f'Getting consumer group offsets for group "{consumer_group}" on topic "{topic}"')

        if not self.is_topic_created(topic):
            raise TopicNotFoundException(topic_name=topic)

        cluster_consumer_groups = self.get_cluster_consumer_groups()
        if consumer_group not in cluster_consumer_groups:
            raise ConsumerGroupNotFoundException(consumer_group=consumer_group)

        partitions = self.get_number_of_partitions(topic)
        topic_partitions = [TopicPartition(topic=topic, partition=partition) for partition in range(partitions)]

        offsets_response = self._get_kafka_admin().list_consumer_group_offsets(
            consumer_group, partitions=topic_partitions
        )

        # Build the result dictionary, filtering out partitions with no committed offset (-1)
        result: dict[int, int] = {}
        for topic_partition, offset_and_metadata in offsets_response.items():
            if offset_and_metadata.offset >= 0:
                result[topic_partition.partition] = offset_and_metadata.offset

        return result
