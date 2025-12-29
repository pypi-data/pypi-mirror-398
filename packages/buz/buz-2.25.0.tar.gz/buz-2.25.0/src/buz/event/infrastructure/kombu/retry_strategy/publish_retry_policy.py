from abc import abstractmethod, ABC

from buz.event import Event


class PublishRetryPolicy(ABC):
    @abstractmethod
    def max_retries(self, event: Event) -> int:
        pass

    @abstractmethod
    def interval_start(self, event: Event) -> float:
        pass

    @abstractmethod
    def interval_step(self, event: Event) -> float:
        pass

    @abstractmethod
    def interval_max(self, event: Event) -> float:
        pass

    @abstractmethod
    def error_callback(self, event: Event, exc: Exception, interval_range: range) -> None:
        pass
