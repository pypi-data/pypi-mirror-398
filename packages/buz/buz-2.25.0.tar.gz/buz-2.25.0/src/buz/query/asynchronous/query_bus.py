from abc import ABC, abstractmethod

from buz.query import Query, QueryResponse


class QueryBus(ABC):
    @abstractmethod
    async def handle(self, query: Query) -> QueryResponse:
        pass
