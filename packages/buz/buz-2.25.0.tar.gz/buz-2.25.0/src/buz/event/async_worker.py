import asyncio
from logging import Logger
from signal import SIGTERM, SIGINT

from buz.event.strategies.execution_strategy.async_execution_strategy import AsyncExecutionStrategy


class AsyncWorker:
    def __init__(
        self,
        logger: Logger,
        execution_strategy: AsyncExecutionStrategy,
    ) -> None:
        self.__execution_strategy = execution_strategy
        self.__logger = logger

    async def start(self) -> None:
        loop = asyncio.get_running_loop()
        loop.add_signal_handler(SIGINT, self.stop)
        loop.add_signal_handler(SIGTERM, self.stop)
        self.__logger.info("Starting buz worker...")
        await self.__execution_strategy.start()
        self.__logger.info("Buz worker stopped gracefully")

    def stop(self) -> None:
        self.__logger.info("Stopping buz worker...")
        self.__execution_strategy.request_stop()
