from dataclasses import dataclass
from typing import Any, Optional


@dataclass(frozen=True)
class CreateKafkaTopic:
    name: str
    partitions: int
    replication_factor: int
    configs: Optional[dict[str, Any]] = None
