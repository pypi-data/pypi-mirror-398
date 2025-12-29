from dataclasses import dataclass, fields
from datetime import datetime
from typing import Any, ClassVar
from uuid import UUID

DlqRecordId = UUID


@dataclass
class DlqRecord:
    __EXCEPTION_MESSAGE_MAX_CHARACTERS: ClassVar[int] = 300
    DATE_TIME_FORMAT: ClassVar[str] = "%Y-%m-%d %H:%M:%S.%f"

    id: DlqRecordId
    event_id: UUID
    subscriber_fqn: str
    event_payload: dict
    exception_type: str
    exception_message: str
    last_failed_at: datetime

    def __post_init__(self) -> None:
        self.exception_message = self.__add_ellipsis(self.exception_message)

    def __add_ellipsis(self, message: str) -> str:
        if len(message) <= self.__EXCEPTION_MESSAGE_MAX_CHARACTERS:
            return message
        return message[: self.__EXCEPTION_MESSAGE_MAX_CHARACTERS - 3] + "..."

    def set_exception(self, exception: Exception) -> None:
        self.exception_type = type(exception).__name__
        self.exception_message = self.__add_ellipsis(str(exception))

    def mark_as_failed(self) -> None:
        self.last_failed_at = datetime.now()

    def get_attrs(self) -> dict[str, Any]:
        attrs = {}
        for field in fields(self):
            property_name = field.name
            property_value = getattr(self, property_name)
            attrs[property_name] = property_value

        return attrs
