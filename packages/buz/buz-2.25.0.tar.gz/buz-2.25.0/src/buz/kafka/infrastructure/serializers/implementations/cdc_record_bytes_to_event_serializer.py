from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
from typing import Optional

from buz.event import Event
from buz.kafka.infrastructure.cdc.cdc_message import CDCMessage, CDCPayload
from buz.kafka.infrastructure.cdc.cdc_schema import generate_cdc_schema
from buz.kafka.infrastructure.serializers.byte_serializer import ByteSerializer
from buz.kafka.infrastructure.serializers.implementations.json_byte_serializer import JSONByteSerializer


class CDCRecordBytesToEventSerializer(ByteSerializer):
    def __init__(self) -> None:
        self.__json_serializer = JSONByteSerializer()

    def serialize(self, data: Event) -> bytes:
        cdc_message: CDCMessage = CDCMessage(
            payload=CDCPayload(
                event_id=data.id,
                created_at=self.__adapt_created_to_cdc_format(data.created_at),
                event_fqn=data.fqn(),
                payload=self.__serialize_payload(data),
                metadata=self.__serialize_metadata(data),
            ),
            schema=generate_cdc_schema(data),
        )
        return self.__json_serializer.serialize(asdict(cdc_message))

    def __adapt_created_to_cdc_format(self, created_at: str) -> str:
        created_at_datetime = datetime.strptime(created_at, Event.DATE_TIME_FORMAT)
        return created_at_datetime.strftime(CDCPayload.DATE_TIME_FORMAT)

    def __serialize_payload(self, event: Event) -> str:
        payload = asdict(event)
        del payload["id"]
        del payload["created_at"]
        del payload["metadata"]
        return self.__json_serializer.serialize_as_json(payload)

    def __serialize_metadata(self, event: Event) -> Optional[str]:
        return self.__json_serializer.serialize_as_json(event.metadata)  # type: ignore[arg-type]
