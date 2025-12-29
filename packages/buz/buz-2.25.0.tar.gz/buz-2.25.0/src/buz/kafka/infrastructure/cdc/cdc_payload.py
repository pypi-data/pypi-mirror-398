from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class CDCPayload:
    DATE_TIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"

    payload: str  # json encoded
    event_id: str  # uuid
    created_at: str
    event_fqn: str
    metadata: Optional[str] = None  # json encoded
    captured_at_ms: Optional[int] = None

    def validate(self) -> None:
        if not isinstance(self.payload, str):
            raise ValueError("The payload value is not a valid value")
        if not isinstance(self.event_id, str):
            raise ValueError("The event_id value is not a valid value")
        if not isinstance(self.created_at, str):
            raise ValueError("The created_at value is not a value")
        if not isinstance(self.event_fqn, str):
            raise ValueError("The event_fqn value is not a valid value")
        if self.metadata is not None and not isinstance(self.metadata, str):
            raise ValueError("The metadata value is not a valid value")
        if self.captured_at_ms is not None and not isinstance(self.captured_at_ms, int):
            raise ValueError("The captured_at_ms value is not a valid value")

    def __post_init__(self) -> None:
        self.validate()
