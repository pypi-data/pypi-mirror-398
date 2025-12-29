from typing import Callable, Coroutine, Union, TypeVar, Generic

from buz.command import Command
from buz.query import Query
from buz.wrapper.event_loop import loop

HandleCallable = Union[Callable[[Command], Coroutine], Callable[[Query], Coroutine]]
T = TypeVar("T")  # Buz input type, Ex: Command, Query, Event
K = TypeVar("K")  # Buz response type, Ex: QueryResponse, None


class AsyncToSync(Generic[T, K]):
    def __init__(self, func: HandleCallable):
        self.__func = func

    def __call__(self, *args: T) -> K:
        return self.__run_task(self.__func, *args)

    @staticmethod
    def __run_task(func: Callable, *args: T) -> K:
        return loop.run_until_complete(func(*args))
