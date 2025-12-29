from buz.event import Event
from buz.event.middleware import PublishMiddleware, PublishCallable
from buz.middleware import MiddlewareChainBuilder


class PublishMiddlewareChainResolver:
    def __init__(self, middlewares: list[PublishMiddleware]):
        self.__middlewares = middlewares
        self.__middleware_chain_builder: MiddlewareChainBuilder[
            PublishCallable, PublishMiddleware
        ] = MiddlewareChainBuilder(middlewares)

    def resolve(self, event: Event, publish: PublishCallable) -> None:
        chain_callable: PublishCallable = self.__middleware_chain_builder.get_chain_callable(
            publish, self.__get_middleware_callable
        )
        chain_callable(event)

    def __get_middleware_callable(
        self, middleware: PublishMiddleware, publish_callable: PublishCallable
    ) -> PublishCallable:
        return lambda event: middleware.on_publish(event, publish_callable)
