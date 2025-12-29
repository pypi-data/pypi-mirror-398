from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from buz.event.event import Event
from buz.event.meta_subscriber import MetaSubscriber

TEvent = TypeVar("TEvent", bound=Event)


class Subscriber(Generic[TEvent], MetaSubscriber[TEvent], ABC):
    @abstractmethod
    def consume(self, event: TEvent) -> None:
        pass
