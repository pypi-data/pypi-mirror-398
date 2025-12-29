from dataclasses import dataclass

from buz import Message


@dataclass(frozen=True)
class Command(Message):
    @classmethod
    def fqn(cls) -> str:
        return f"command.{super().fqn()}"
