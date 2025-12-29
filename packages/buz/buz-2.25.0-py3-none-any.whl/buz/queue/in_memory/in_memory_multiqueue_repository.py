from queue import Queue, Empty
from typing import Optional, TypeVar, cast

from buz.queue.multiqueue_repository import MultiqueueRepository

K = TypeVar("K")
R = TypeVar("R")


class InMemoryMultiqueueRepository(MultiqueueRepository[K, R]):
    def __init__(self):
        self.__queues = cast(dict[K, Queue[R]], {})
        self.__last_key_index = 0

    def create_key(self, key: K) -> None:
        self.__queues[key] = Queue[R]()

    def remove_key(self, key: K) -> None:
        if key not in self.__queues:
            return

        self.__queues.pop(key)

    def push(self, key: K, record: R) -> None:
        if key not in self.__queues:
            return

        queue = self.__queues[key]
        queue.put(record)

    def pop(self) -> Optional[R]:
        if not self.__queues:
            return None

        queue_keys = list(self.__queues.keys())
        num_queues = len(queue_keys)

        for _ in range(num_queues):
            new_key_index = (self.__last_key_index + 1) % num_queues

            key = queue_keys[new_key_index]
            queue = self.__queues[key]

            self.__last_key_index = new_key_index

            try:
                record = queue.get(block=False)
                return record
            except (Empty, ValueError, AttributeError):
                continue

        return None

    def get_total_size(self) -> int:
        return sum([queue.qsize() for queue in self.__queues.values()])

    def is_totally_empty(self) -> bool:
        return all([queue.empty() for queue in self.__queues.values()])
