from typing import Type, TypeVar, cast

from buz import Message
from buz.kafka.infrastructure.deserializers.bytes_to_message_deserializer import BytesToMessageDeserializer
from buz.kafka.infrastructure.deserializers.implementations.json_byte_deserializer import JSONByteDeserializer

T = TypeVar("T", bound=Message)


class JSONBytesToMessageDeserializer(BytesToMessageDeserializer[T]):
    def __init__(
        self,
        *,
        event_class: Type[T],
    ):
        self.__event_class = event_class
        self.__json_byte_deserializer = JSONByteDeserializer()

    def deserialize(self, data: bytes) -> T:
        dictionary = self.__json_byte_deserializer.deserialize(data=data)
        return cast(T, self.__event_class.restore(**dictionary))
