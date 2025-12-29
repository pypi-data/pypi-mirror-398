from buz.event.consumer import Consumer
from buz.event.strategies.execution_strategy.execution_strategy import ExecutionStrategy


class SelfProcessExecutionStrategy(ExecutionStrategy):
    def __init__(self, consumer: Consumer):
        self.__consumer = consumer

    def start(self) -> None:
        self.__consumer.run()

    def stop(self) -> None:
        self.__consumer.stop()
