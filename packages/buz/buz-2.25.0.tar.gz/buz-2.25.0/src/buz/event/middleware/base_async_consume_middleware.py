from abc import abstractmethod

from buz.event import Event
from buz.event.async_subscriber import AsyncSubscriber
from buz.event.infrastructure.models.execution_context import ExecutionContext
from buz.event.middleware.async_consume_middleware import AsyncConsumeMiddleware, AsyncConsumeCallable


class BaseAsyncConsumeMiddleware(AsyncConsumeMiddleware):
    async def on_consume(
        self,
        event: Event,
        subscriber: AsyncSubscriber,
        consume: AsyncConsumeCallable,
        execution_context: ExecutionContext,
    ) -> None:
        await self._before_on_consume(event, subscriber, execution_context)
        await consume(event, subscriber, execution_context)
        await self._after_on_consume(event, subscriber, execution_context)

    @abstractmethod
    async def _before_on_consume(
        self,
        event: Event,
        subscriber: AsyncSubscriber,
        execution_context: ExecutionContext,
    ) -> None:
        pass

    @abstractmethod
    async def _after_on_consume(
        self,
        event: Event,
        subscriber: AsyncSubscriber,
        execution_context: ExecutionContext,
    ) -> None:
        pass
