from abc import ABC, abstractmethod
from typing import Generic, Optional, TypeVar

K = TypeVar("K")
R = TypeVar("R")


class MultiqueueRepository(ABC, Generic[K, R]):
    @abstractmethod
    def create_key(self, key: K) -> None:
        pass

    @abstractmethod
    def remove_key(self, key: K) -> None:
        pass

    @abstractmethod
    def push(self, key: K, record: R) -> None:
        pass

    @abstractmethod
    def pop(self) -> Optional[R]:
        pass

    @abstractmethod
    def get_total_size(self) -> int:
        pass

    @abstractmethod
    def is_totally_empty(self) -> bool:
        pass
