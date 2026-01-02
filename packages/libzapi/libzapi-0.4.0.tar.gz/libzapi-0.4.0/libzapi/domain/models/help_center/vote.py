from dataclasses import dataclass
from datetime import datetime

from libzapi.domain.shared_objects.logical_key import LogicalKey


@dataclass(frozen=True, slots=True)
class Vote:
    id: int
    url: str
    item_id: int
    item_type: str
    user_id: int
    value: int
    created_at: datetime
    updated_at: datetime

    @property
    def logical_key(self) -> LogicalKey:
        base = f"id_{self.id}"
        return LogicalKey("vote", base)
