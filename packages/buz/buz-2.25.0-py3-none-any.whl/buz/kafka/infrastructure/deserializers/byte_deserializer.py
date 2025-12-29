from abc import ABC, abstractmethod
from typing import Generic, TypeVar

T = TypeVar("T")


class ByteDeserializer(ABC, Generic[T]):
    @abstractmethod
    def deserialize(self, data: bytes) -> T:
        pass
