from dataclasses import dataclass

from buz.event.infrastructure.models.delivery_context import DeliveryContext
from buz.event.infrastructure.models.process_context import ProcessContext


@dataclass(frozen=True)
class ExecutionContext:
    delivery_context: DeliveryContext
    process_context: ProcessContext
