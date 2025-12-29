from dataclasses import dataclass
from buz.kafka.domain.models.kafka_poll_record import KafkaPollRecord
from buz.kafka.infrastructure.aiokafka.aiokafka_consumer import AIOKafkaConsumer


@dataclass(frozen=True)
class ConsumingTask:
    consumer: AIOKafkaConsumer
    kafka_poll_record: KafkaPollRecord
