from abc import ABC, abstractmethod
from typing import Sequence

from buz.event import Event
from buz.event.meta_subscriber import MetaSubscriber


class RejectCallback(ABC):
    @abstractmethod
    def on_reject(self, event: Event, subscribers: Sequence[MetaSubscriber], exception: Exception) -> None:
        pass
