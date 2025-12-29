from abc import ABC, abstractmethod


class Consumer(ABC):
    @abstractmethod
    def run(self) -> None:
        pass

    @abstractmethod
    def stop(self) -> None:
        pass
