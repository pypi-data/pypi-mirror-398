from buz.event import Event
from buz.event.middleware.async_publish_middleware import AsyncPublishCallable, AsyncPublishMiddleware
from buz.middleware import MiddlewareChainBuilder


class AsyncPublishMiddlewareChainResolver:
    def __init__(self, middlewares: list[AsyncPublishMiddleware]):
        self.__middlewares = middlewares
        self.__middleware_chain_builder: MiddlewareChainBuilder[
            AsyncPublishCallable, AsyncPublishMiddleware
        ] = MiddlewareChainBuilder(middlewares)

    async def resolve(self, event: Event, publish: AsyncPublishCallable) -> None:
        chain_callable: AsyncPublishCallable = self.__middleware_chain_builder.get_chain_callable(
            publish, self.__get_middleware_callable
        )
        await chain_callable(event)

    def __get_middleware_callable(
        self, middleware: AsyncPublishMiddleware, publish_callable: AsyncPublishCallable
    ) -> AsyncPublishCallable:
        return lambda event: middleware.on_publish(event, publish_callable)
