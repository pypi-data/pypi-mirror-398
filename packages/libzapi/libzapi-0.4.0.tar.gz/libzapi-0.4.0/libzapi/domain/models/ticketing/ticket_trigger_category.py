from dataclasses import dataclass
from datetime import datetime

from libzapi.domain.shared_objects.logical_key import LogicalKey


@dataclass(frozen=True, slots=True)
class TicketTriggerCategory:
    id: int
    url: str
    name: str
    updated_at: datetime
    created_at: datetime
    position: int

    @property
    def logical_key(self) -> LogicalKey:
        base = self.name.lower().replace(" ", "_")
        return LogicalKey("ticket_trigger_category", base)
