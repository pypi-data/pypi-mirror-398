from abc import abstractmethod
from typing import Awaitable, Callable

from buz.event import Event
from buz.event.async_subscriber import AsyncSubscriber
from buz.event.infrastructure.models.execution_context import ExecutionContext
from buz.middleware import Middleware

AsyncConsumeCallable = Callable[[Event, AsyncSubscriber, ExecutionContext], Awaitable[None]]


class AsyncConsumeMiddleware(Middleware):
    @abstractmethod
    async def on_consume(
        self,
        event: Event,
        subscriber: AsyncSubscriber,
        consume: AsyncConsumeCallable,
        execution_context: ExecutionContext,
    ) -> None:
        pass
