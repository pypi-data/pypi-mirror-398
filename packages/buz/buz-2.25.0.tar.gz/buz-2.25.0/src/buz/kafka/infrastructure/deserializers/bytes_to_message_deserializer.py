from abc import abstractmethod
from typing import TypeVar

from buz.kafka.infrastructure.deserializers.byte_deserializer import ByteDeserializer
from buz.message import Message

T = TypeVar("T", bound=Message)


class BytesToMessageDeserializer(ByteDeserializer[T]):
    @abstractmethod
    def deserialize(self, data: bytes) -> T:
        pass
