from abc import ABC, abstractmethod
from typing import Iterable

from buz.event import Event


class EventBus(ABC):
    @abstractmethod
    def publish(self, event: Event) -> None:
        pass

    @abstractmethod
    def bulk_publish(self, events: Iterable[Event]) -> None:
        pass
