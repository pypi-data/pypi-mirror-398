from abc import abstractmethod
from typing import Callable

from buz.middleware import Middleware
from buz.query import Query, QueryResponse
from buz.query.synchronous import QueryHandler

HandleCallable = Callable[[Query, QueryHandler], QueryResponse]


class HandleMiddleware(Middleware):
    @abstractmethod
    def on_handle(self, query: Query, query_handler: QueryHandler, handle: HandleCallable) -> QueryResponse:
        pass
