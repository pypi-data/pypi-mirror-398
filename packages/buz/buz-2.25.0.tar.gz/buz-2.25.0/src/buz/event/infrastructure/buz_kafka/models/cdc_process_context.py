from dataclasses import dataclass
from typing import Optional

from buz.event.infrastructure.models.process_context import ProcessContext


@dataclass(frozen=True)
class CDCProcessContext(ProcessContext):
    captured_at_ms: Optional[int] = None
