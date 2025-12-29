from abc import ABC

from buz.kafka.domain.models.kafka_poll_record import KafkaPollRecord


class KafkaEventSubscriberExecutor(ABC):
    async def consume(
        self,
        *,
        kafka_poll_record: KafkaPollRecord,
    ) -> None:
        pass
