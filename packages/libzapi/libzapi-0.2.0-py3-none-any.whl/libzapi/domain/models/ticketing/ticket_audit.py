from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

from libzapi.domain.shared_objects.via import Via
from libzapi.domain.shared_objects.logical_key import LogicalKey


@dataclass(frozen=True, slots=True)
class TicketAudit:
    id: int
    author_id: int
    created_at: datetime
    events: Iterable[dict]
    metadata: dict
    ticket_id: int
    via: Via

    @property
    def logical_key(self) -> LogicalKey:
        base = f"ticket_audit_{self.id}"
        return LogicalKey("ticket_audit", base)
