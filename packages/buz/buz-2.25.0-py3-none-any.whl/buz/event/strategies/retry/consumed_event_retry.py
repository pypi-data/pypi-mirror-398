from dataclasses import dataclass


@dataclass
class ConsumedEventRetry:
    event_id: str
    subscribers_fqns: list[str]
    retries: int

    def register_retry(self) -> None:
        self.retries += 1
