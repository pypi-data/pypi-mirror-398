from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class QueryResponse:  # type: ignore
    content: Any  # type: ignore
