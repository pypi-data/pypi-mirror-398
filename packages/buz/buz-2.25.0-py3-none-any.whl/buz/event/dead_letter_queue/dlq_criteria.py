from dataclasses import dataclass
from typing import ClassVar, Union

from buz.event.dead_letter_queue.dlq_record import DlqRecordId


@dataclass(frozen=True)
class DlqCriteria:
    UNSET_VALUE: ClassVar[object] = object()

    dlq_record_id: Union[DlqRecordId, None, object] = UNSET_VALUE
