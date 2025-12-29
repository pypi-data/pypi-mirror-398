from dataclasses import dataclass
from typing import Optional

from buz.kafka.infrastructure.cdc.cdc_payload import CDCPayload


@dataclass(frozen=True)
class CDCMessage:
    payload: CDCPayload
    schema: Optional[dict]

    def validate(self) -> None:
        if not isinstance(self.payload, CDCPayload):
            raise ValueError("The payload value is not a valid value")
        if self.schema is not None and not isinstance(self.schema, dict):
            raise ValueError("The schema value is not a valid value")

    def __post_init__(self) -> None:
        self.validate()
