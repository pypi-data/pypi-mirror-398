from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class AutoCreateTopicConfiguration:
    partitions: int
    replication_factor: int
    configs: dict[str, Any]
