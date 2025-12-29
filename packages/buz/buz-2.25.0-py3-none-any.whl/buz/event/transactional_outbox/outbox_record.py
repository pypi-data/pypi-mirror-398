from dataclasses import dataclass, fields
from datetime import datetime
from typing import Any, ClassVar
from uuid import UUID


@dataclass
class OutboxRecord:  # type: ignore[misc]
    DATE_TIME_FORMAT: ClassVar[str] = "%Y-%m-%d %H:%M:%S.%f"

    event_id: UUID
    event_fqn: str
    event_payload: dict[str, Any]  # type: ignore[misc]
    created_at: datetime
    event_metadata: dict[str, Any] | None = None
    delivered_at: datetime | None = None
    delivery_errors: int = 0
    delivery_paused_at: datetime | None = None
    partition_key: str | None = None

    def parsed_created_at(self) -> str:
        return self.created_at.strftime(self.DATE_TIME_FORMAT)

    def mark_delivery_error(self) -> None:
        self.delivered_at = None
        self.delivery_errors += 1

    def mark_as_delivered(self) -> None:
        self.delivered_at = datetime.now()

    def pause_delivery(self) -> None:
        self.delivery_paused_at = datetime.now()

    def get_attrs(self) -> dict[str, Any]:
        attrs = {}
        for field in fields(self):
            property_name = field.name
            property_value = getattr(self, property_name)
            attrs[property_name] = property_value

        return attrs
