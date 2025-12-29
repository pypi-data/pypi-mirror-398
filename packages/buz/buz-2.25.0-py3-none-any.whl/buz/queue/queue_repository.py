from abc import ABC, abstractmethod
from typing import Generic, TypeVar

T = TypeVar("T")


class QueueRepository(ABC, Generic[T]):
    @abstractmethod
    def push(self, record: T):
        pass

    @abstractmethod
    def pop(self) -> T:
        pass

    @abstractmethod
    def get_size(self) -> int:
        pass

    @abstractmethod
    def is_empty(self) -> bool:
        pass
