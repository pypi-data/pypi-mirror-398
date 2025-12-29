from __future__ import annotations

from abc import abstractmethod, ABC
from datetime import datetime
from typing import Sequence, Any, Optional

from buz.kafka.domain.models.create_kafka_topic import CreateKafkaTopic
from buz.kafka.infrastructure.interfaces.connection_manager import ConnectionManager

DEFAULT_NUMBER_OF_MESSAGES_TO_POLLING = 999


class KafkaAdminClient(ConnectionManager, ABC):
    @abstractmethod
    def create_topics(
        self,
        *,
        topics: Sequence[CreateKafkaTopic],
    ) -> None:
        pass

    @abstractmethod
    def is_topic_created(
        self,
        topic: str,
    ) -> bool:
        pass

    @abstractmethod
    def delete_topics(
        self,
        *,
        topics: set[str],
    ) -> None:
        pass

    @abstractmethod
    def get_topics(
        self,
    ) -> set[str]:
        pass

    @abstractmethod
    def get_number_of_partitions(self, topic: str) -> int:
        pass

    # This function moves the following offset from the provided date
    # if there are no messages with a date greater than the provided offset
    # the offset will be moved to the end
    @abstractmethod
    def move_offsets_to_datetime(
        self,
        *,
        consumer_group: str,
        topic: str,
        target_datetime: datetime,
    ) -> None:
        pass

    @abstractmethod
    def increase_topic_partitions_and_set_offset_of_related_consumer_groups_to_the_beginning_of_the_new_ones(
        self,
        *,
        topic: str,
        new_number_of_partitions: int,
        consumer_groups_to_ignore: Optional[set[str]] = None,
    ) -> None:
        pass

    @abstractmethod
    def delete_subscription_groups(
        self,
        *,
        subscription_groups: set[str],
    ) -> list[tuple[str, Any]]:
        pass

    @abstractmethod
    def get_consumer_group_offsets(self, *, consumer_group: str, topic: str) -> dict[int, int]:
        """
        Get the committed offsets for a consumer group on a specific topic.
        Returns a dictionary mapping partition numbers to their committed offsets.
        """
        pass
