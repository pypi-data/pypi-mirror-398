from abc import ABC, abstractmethod
from typing import Sequence

from buz.event import Event

from buz.event.meta_subscriber import MetaSubscriber
from buz.event.strategies.retry.consumed_event_retry import ConsumedEventRetry


class ConsumedEventRetryRepository(ABC):
    @abstractmethod
    def save(self, consumed_event_retry: ConsumedEventRetry) -> None:
        pass

    @abstractmethod
    def find_one_by_event_and_subscriber(
        self, event: Event, subscribers: Sequence[MetaSubscriber]
    ) -> ConsumedEventRetry:
        pass

    @abstractmethod
    def clean(self, event: Event, subscribers: Sequence[MetaSubscriber]) -> None:
        pass
