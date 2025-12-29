from abc import abstractmethod

from buz.query import Query, QueryResponse
from buz.query.asynchronous.query_handler import QueryHandler
from buz.query.asynchronous.middleware.handle_middleware import HandleCallable, HandleMiddleware


class BaseHandleMiddleware(HandleMiddleware):
    async def on_handle(self, query: Query, query_handler: QueryHandler, handle: HandleCallable) -> QueryResponse:
        self._before_on_handle(query, query_handler)
        query_response = await handle(query, query_handler)
        return self._after_on_handle(query, query_handler, query_response)

    @abstractmethod
    def _before_on_handle(self, query: Query, query_handler: QueryHandler) -> None:
        pass

    @abstractmethod
    def _after_on_handle(
        self, query: Query, query_handler: QueryHandler, query_response: QueryResponse
    ) -> QueryResponse:
        pass
