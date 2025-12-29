from abc import ABC, abstractmethod
from typing import Collection

from buz.event import Event
from buz.kafka.infrastructure.interfaces.async_connection_manager import AsyncConnectionManager


class AsyncEventBus(AsyncConnectionManager, ABC):
    @abstractmethod
    async def publish(self, event: Event) -> None:
        pass

    @abstractmethod
    async def bulk_publish(self, events: Collection[Event]) -> None:
        pass
