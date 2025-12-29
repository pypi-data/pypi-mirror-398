from abc import abstractmethod
from typing import Awaitable, Callable

from buz.event import Event
from buz.middleware import Middleware

AsyncPublishCallable = Callable[[Event], Awaitable[None]]


class AsyncPublishMiddleware(Middleware):
    @abstractmethod
    async def on_publish(self, event: Event, publish: AsyncPublishCallable) -> None:
        pass
