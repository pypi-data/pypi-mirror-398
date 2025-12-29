from __future__ import annotations

from datetime import datetime
from typing import Optional, TypeVar, Type, Generic

import orjson

from buz.event import Event
from buz.kafka.infrastructure.cdc.cdc_message import CDCPayload
from buz.kafka.infrastructure.deserializers.bytes_to_message_deserializer import BytesToMessageDeserializer
from buz.kafka.infrastructure.deserializers.implementations.cdc.cannot_restore_event_from_cdc_payload_exception import (
    CannotRestoreEventFromCDCPayloadException,
)
from buz.kafka.infrastructure.deserializers.implementations.cdc.cdc_record_bytes_to_cdc_payload_deserializer import (
    CDCRecordBytesToCDCPayloadDeserializer,
)

T = TypeVar("T", bound=Event)


class CDCRecordBytesToEventDeserializer(BytesToMessageDeserializer[Event], Generic[T]):
    __STRING_ENCODING = "utf-8"

    def __init__(self, event_class: Type[T]) -> None:
        self.__event_class = event_class
        self.__cdc_record_bytes_to_cdc_payload_deserializer = CDCRecordBytesToCDCPayloadDeserializer()

    def deserialize(self, data: bytes) -> T:
        cdc_payload = self.__cdc_record_bytes_to_cdc_payload_deserializer.deserialize(data)
        try:
            payload_dict = orjson.loads(cdc_payload.payload)
            return self.__event_class.restore(
                id=cdc_payload.event_id,
                created_at=self.__get_created_at_in_event_format(cdc_payload.created_at),
                metadata=self.__deserialize_metadata(cdc_payload.metadata),
                **payload_dict,
            )
        except Exception as exception:
            raise CannotRestoreEventFromCDCPayloadException(cdc_payload, exception) from exception

    def __get_created_at_in_event_format(self, cdc_payload_created_at: str) -> str:
        created_at_datetime = datetime.strptime(cdc_payload_created_at, CDCPayload.DATE_TIME_FORMAT)
        return created_at_datetime.strftime(Event.DATE_TIME_FORMAT)

    def __deserialize_metadata(self, metadata: Optional[str]) -> dict:
        if metadata is None:
            return {}
        return orjson.loads(metadata)
