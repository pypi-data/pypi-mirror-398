from __future__ import annotations

from abc import abstractmethod, ABC
from typing import Optional

from buz.kafka.domain.models.kafka_poll_record import KafkaPollRecord
from buz.kafka.domain.services.kafka_admin_client import KafkaAdminClient
from buz.kafka.domain.models.consumer_initial_offset_position import ConsumerInitialOffsetPosition

DEFAULT_NUMBER_OF_MESSAGES_TO_POLL = 999


class KafkaAdminTestClient(KafkaAdminClient, ABC):
    @abstractmethod
    def send_message_to_topic(
        self,
        *,
        topic: str,
        message: bytes,
        headers: Optional[list[tuple[str, bytes]]] = None,
        partition_key: Optional[str] = None,
    ) -> None:
        """
        This method was not though as a producer itself, it offers a way to send messages to a topic, that could be useful specially for test purposes
        """
        pass

    @abstractmethod
    def get_messages_from_topic(
        self,
        *,
        topic: str,
        consumer_group: str,
        max_number_of_messages_to_polling: int = DEFAULT_NUMBER_OF_MESSAGES_TO_POLL,
        offset: ConsumerInitialOffsetPosition = ConsumerInitialOffsetPosition.BEGINNING,
    ) -> list[KafkaPollRecord]:
        """
        This method is not though as a consumer itself, it offers a way to get messages from a topic, that could be useful specially for test purposes
        """
        pass

    @abstractmethod
    def delete_all_resources(
        self,
    ) -> None:
        """
        Only for test purposes, remove all the resources related to the kafka cluster, like topics, subscription groups
        """
        pass
