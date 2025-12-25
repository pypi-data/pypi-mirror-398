from dataclasses import dataclass
from datetime import datetime

from libzapi.domain.shared_objects.logical_key import LogicalKey


@dataclass(frozen=True, slots=True)
class Session:
    id: int
    url: str
    user_id: int
    authenticated_at: datetime
    last_seen_at: datetime

    @property
    def logical_key(self) -> LogicalKey:
        base = f"session_id_{self.id}"
        return LogicalKey("session", base)
