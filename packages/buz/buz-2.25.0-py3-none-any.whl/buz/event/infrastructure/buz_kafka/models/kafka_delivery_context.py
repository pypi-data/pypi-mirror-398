from dataclasses import dataclass
from buz.event.infrastructure.models.delivery_context import DeliveryContext


@dataclass(frozen=True)
class KafkaDeliveryContext(DeliveryContext):
    topic: str
    consumer_group: str
    partition: int
    timestamp: int
