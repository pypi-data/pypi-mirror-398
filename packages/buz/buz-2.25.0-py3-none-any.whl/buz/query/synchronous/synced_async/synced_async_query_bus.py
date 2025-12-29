from buz.query import QueryResponse, Query
from buz.query.synchronous import QueryBus
from buz.query.asynchronous import QueryBus as AsynchronousQueryBus
from buz.wrapper import AsyncToSync


class SyncedAsyncQueryBus(QueryBus):
    def __init__(self, async_bus: AsynchronousQueryBus):
        self.__wrapped_handler = AsyncToSync[Query, QueryResponse](async_bus.handle)

    def handle(self, query: Query) -> QueryResponse:
        return self.__wrapped_handler(query)
