from buz.middleware.middleware_chain_builder import MiddlewareChainBuilder
from buz.query import Query, QueryResponse
from buz.query.asynchronous import QueryHandler
from buz.query.asynchronous.middleware.handle_middleware import HandleMiddleware, HandleCallable


class HandleMiddlewareChainResolver:
    def __init__(self, middlewares: list[HandleMiddleware]):
        self.__middlewares = middlewares
        self.__middleware_chain_builder: MiddlewareChainBuilder[
            HandleCallable, HandleMiddleware
        ] = MiddlewareChainBuilder(middlewares)

    async def resolve(self, query: Query, query_handler: QueryHandler, handle: HandleCallable) -> QueryResponse:
        chain_callable: HandleCallable = self.__middleware_chain_builder.get_chain_callable(
            handle, self.__get_middleware_callable
        )
        return await chain_callable(query, query_handler)

    @staticmethod
    def __get_middleware_callable(middleware: HandleMiddleware, next_callable: HandleCallable) -> HandleCallable:
        return lambda query, query_handler: middleware.on_handle(query, query_handler, next_callable)
