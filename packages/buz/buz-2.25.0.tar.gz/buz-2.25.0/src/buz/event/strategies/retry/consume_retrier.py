from abc import ABC, abstractmethod
from typing import Sequence
from buz.event import Event
from buz.event.meta_subscriber import MetaSubscriber


class ConsumeRetrier(ABC):
    @abstractmethod
    def should_retry(self, event: Event, subscribers: Sequence[MetaSubscriber]) -> bool:
        pass

    @abstractmethod
    def register_retry(self, event: Event, subscribers: Sequence[MetaSubscriber]) -> None:
        pass

    @abstractmethod
    def clean_retries(self, event: Event, subscribers: Sequence[MetaSubscriber]) -> None:
        pass
