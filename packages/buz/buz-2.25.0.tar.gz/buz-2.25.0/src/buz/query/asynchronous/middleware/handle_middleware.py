from abc import abstractmethod
from typing import Callable, Awaitable

from buz.middleware import Middleware
from buz.query import Query, QueryResponse
from buz.query.asynchronous import QueryHandler

HandleCallable = Callable[[Query, QueryHandler], Awaitable[QueryResponse]]


class HandleMiddleware(Middleware):
    @abstractmethod
    async def on_handle(self, query: Query, query_handler: QueryHandler, handle: HandleCallable) -> QueryResponse:
        pass
