from queue import Queue
from typing import TypeVar

from buz.queue.queue_repository import QueueRepository


T = TypeVar("T")


class InMemoryQueueRepository(QueueRepository[T]):
    def __init__(self, queue: Queue[T]):
        self._queue = queue

    def push(self, record: T):
        self._queue.put(record)

    def pop(self) -> T:
        return self._queue.get()

    def get_size(self) -> int:
        return self._queue.qsize()

    def is_empty(self) -> bool:
        return self._queue.empty()
