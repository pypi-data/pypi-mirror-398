from typing import Sequence
from buz.event import Event, Subscriber
from buz.event.infrastructure.models.execution_context import ExecutionContext
from buz.event.middleware import ConsumeMiddleware, ConsumeCallable
from buz.middleware import MiddlewareChainBuilder


class ConsumeMiddlewareChainResolver:
    def __init__(self, middlewares: Sequence[ConsumeMiddleware]):
        self.__middlewares = middlewares
        self.__middleware_chain_builder: MiddlewareChainBuilder[
            ConsumeCallable, ConsumeMiddleware
        ] = MiddlewareChainBuilder(self.__middlewares)

    def resolve(
        self,
        event: Event,
        subscriber: Subscriber,
        consume: ConsumeCallable,
        execution_context: ExecutionContext,
    ) -> None:
        chain_callable: ConsumeCallable = self.__middleware_chain_builder.get_chain_callable(
            consume, self.__get_middleware_callable
        )
        chain_callable(event, subscriber, execution_context)

    def __get_middleware_callable(
        self, middleware: ConsumeMiddleware, consume_callable: ConsumeCallable
    ) -> ConsumeCallable:
        return lambda event, subscriber, execution_context: middleware.on_consume(
            event, subscriber, consume_callable, execution_context
        )
