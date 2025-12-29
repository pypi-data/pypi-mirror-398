from abc import abstractmethod
from typing import TypeVar

from buz.kafka.infrastructure.serializers.byte_serializer import ByteSerializer
from buz.message import Message

T = TypeVar("T", bound=Message)


class MessageToByteSerializer(ByteSerializer[T]):
    @abstractmethod
    def serialize(self, data: T) -> bytes:
        pass
