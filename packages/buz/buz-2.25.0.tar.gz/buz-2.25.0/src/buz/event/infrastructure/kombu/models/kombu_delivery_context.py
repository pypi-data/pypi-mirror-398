from dataclasses import dataclass
from buz.event.infrastructure.models.delivery_context import DeliveryContext


@dataclass(frozen=True)
class KombuDeliveryContext(DeliveryContext):
    pass
