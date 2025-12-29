from dataclasses import dataclass

from buz import Message


@dataclass(frozen=True)
class Query(Message):
    @classmethod
    def fqn(cls) -> str:
        return f"query.{super().fqn()}"
