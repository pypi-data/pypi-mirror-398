from abc import abstractmethod
from typing import Callable

from buz.event import Event, Subscriber
from buz.event.infrastructure.models.execution_context import ExecutionContext
from buz.middleware import Middleware

ConsumeCallable = Callable[[Event, Subscriber, ExecutionContext], None]


class ConsumeMiddleware(Middleware):
    @abstractmethod
    def on_consume(
        self, event: Event, subscriber: Subscriber, consume: ConsumeCallable, execution_context: ExecutionContext
    ) -> None:
        pass
