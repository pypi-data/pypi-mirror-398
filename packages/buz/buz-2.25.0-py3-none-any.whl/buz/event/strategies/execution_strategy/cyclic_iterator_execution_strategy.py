from itertools import cycle

from buz.event.consumer import Consumer
from buz.event.strategies.execution_strategy.execution_strategy import ExecutionStrategy


class CyclicIteratorExecutionStrategy(ExecutionStrategy):
    def __init__(self, consumers: list[Consumer]):
        self.__consumers: list[Consumer] = consumers
        self.__stop_requested = False

    def start(self) -> None:
        active_consumers: set[Consumer] = set(self.__consumers)

        for consumer in cycle(self.__consumers):
            if consumer not in active_consumers:
                continue
            consumer.run()
            if self.__stop_requested is True:
                active_consumers.remove(consumer)
            if not active_consumers:
                break

    def stop(self) -> None:
        for consumer in self.__consumers:
            consumer.stop()
        self.__stop_requested = True
