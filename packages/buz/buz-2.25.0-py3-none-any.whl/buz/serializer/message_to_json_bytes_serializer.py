from dataclasses import asdict
from typing import Type, TypeVar, cast

from buz.event import Event
from buz.kafka.infrastructure.serializers.implementations.json_byte_serializer import (
    JSON_SERIALIZABLE,
    JSONByteSerializer,
)
from buz.serializer.message_to_bytes_serializer import MessageToByteSerializer

T = TypeVar("T", bound=Event)


class MessageClassToJSONByteSerializer(MessageToByteSerializer[T]):
    def __init__(
        self,
        *,
        event_class: Type[T],
    ):
        self.__event_class = event_class
        self.__json_byte_serializer = JSONByteSerializer()

    def serialize(self, data: T) -> bytes:
        dictionary = cast(JSON_SERIALIZABLE, asdict(data))
        return self.__json_byte_serializer.serialize(dictionary)
