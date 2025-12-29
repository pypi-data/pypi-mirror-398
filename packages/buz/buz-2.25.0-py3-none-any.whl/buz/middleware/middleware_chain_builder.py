from typing import Callable, Generic, Sequence, TypeVar, Optional

from buz.middleware import Middleware

C = TypeVar("C", bound=Callable)
M = TypeVar("M", bound=Middleware)


class MiddlewareChainBuilder(Generic[C, M]):
    def __init__(self, middlewares: Sequence[M]):
        self.__chain_callable: Optional[C] = None
        self.__middlewares = middlewares

    def get_chain_callable(self, base_case_callable: C, middleware_call: Callable[[M, C], C]) -> C:
        if self.__chain_callable is None:
            self.__chain_callable = self.__get_next_callable(0, base_case_callable, middleware_call)
        return self.__chain_callable

    def __get_next_callable(self, index: int, base_case_callable: C, middleware_call: Callable[[M, C], C]) -> C:
        if index == len(self.__middlewares):
            return base_case_callable
        next_callable = self.__get_next_callable(index + 1, base_case_callable, middleware_call)
        return middleware_call(self.__middlewares[index], next_callable)
