from typing import Generic, Type, TypeVar, cast, get_type_hints, Any

from buz.query import Query
from buz.query.asynchronous.query_handler import QueryHandler
from buz.query.query_response import QueryResponse

TQuery = TypeVar("TQuery", bound=Query)
TQueryResponse = TypeVar("TQueryResponse", bound=QueryResponse)


class BaseQueryHandler(Generic[TQuery, TQueryResponse], QueryHandler[TQuery, TQueryResponse]):
    @classmethod
    def fqn(cls) -> str:
        return f"query_handler.{cls.__module__}.{cls.__name__}"

    @classmethod
    def handles(cls) -> Type[TQuery]:
        handle_types = get_type_hints(cls.handle)

        t_query = handle_types.get("query")
        if t_query is None:
            raise TypeError(
                f"The method 'handle' in '{cls.fqn()}' doesn't have a parameter named 'query'. Found parameters: {cls.__get_method_parameter_names(handle_types)}"
            )

        # TypeVar mask the actual bound type
        if hasattr(t_query, "__bound__"):
            t_query = t_query.__bound__

        if not issubclass(t_query, Query):
            raise TypeError(f"The parameter 'query' in '{cls.fqn()}.handle' is not a 'buz.query.Query' subclass")

        return cast(Type[TQuery], t_query)

    @classmethod
    def __get_method_parameter_names(cls, handle_types: dict[str, Any]) -> list[str]:
        handle_types_copy: dict = handle_types.copy()
        handle_types_copy.pop("return", None)
        return list(handle_types_copy.keys())
