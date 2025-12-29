from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Union


@dataclass(frozen=True)
class KafkaPollRecord:
    key: Optional[Union[str, bytes]]
    headers: list[tuple[str, bytes]]
    value: Optional[bytes]
    timestamp: int
    partition: int
    topic: str
    offset: int
