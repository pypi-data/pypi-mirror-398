from abc import abstractmethod

from buz.event import Event, Subscriber
from buz.event.infrastructure.models.execution_context import ExecutionContext
from buz.event.middleware import ConsumeMiddleware, ConsumeCallable


class BaseConsumeMiddleware(ConsumeMiddleware):
    def on_consume(
        self, event: Event, subscriber: Subscriber, consume: ConsumeCallable, execution_context: ExecutionContext
    ) -> None:
        self._before_on_consume(event, subscriber, execution_context)
        consume(event, subscriber, execution_context)
        self._after_on_consume(event, subscriber, execution_context)

    @abstractmethod
    def _before_on_consume(self, event: Event, subscriber: Subscriber, execution_context: ExecutionContext) -> None:
        pass

    @abstractmethod
    def _after_on_consume(self, event: Event, subscriber: Subscriber, execution_context: ExecutionContext) -> None:
        pass
