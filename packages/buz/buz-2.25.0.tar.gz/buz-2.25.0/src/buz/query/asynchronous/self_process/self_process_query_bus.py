from typing import Optional

from buz.locator import Locator
from buz.query import Query, QueryResponse
from buz.query.asynchronous import QueryBus
from buz.query.asynchronous import QueryHandler
from buz.query.asynchronous.middleware import HandleMiddleware, HandleMiddlewareChainResolver
from buz.query import MoreThanOneQueryHandlerRelatedException


class SelfProcessQueryBus(QueryBus):
    def __init__(
        self,
        locator: Locator[Query, QueryHandler],
        middlewares: Optional[list[HandleMiddleware]] = None,
    ):
        self.__locator = locator
        self.__handle_middleware_chain_resolver = HandleMiddlewareChainResolver(middlewares or [])

    async def handle(self, query: Query) -> QueryResponse:
        query_handlers = self.__locator.get(query)

        if len(query_handlers) > 1:
            raise MoreThanOneQueryHandlerRelatedException(query, query_handlers)

        query_handler = query_handlers[0]
        return await self.__handle_middleware_chain_resolver.resolve(query, query_handler, self.__perform_handle)

    @staticmethod
    async def __perform_handle(query: Query, query_handler: QueryHandler) -> QueryResponse:
        return await query_handler.handle(query)
