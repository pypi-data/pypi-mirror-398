from dataclasses import dataclass
from datetime import datetime

from libzapi.domain.shared_objects.logical_key import LogicalKey


@dataclass(frozen=True, slots=True)
class BadgeAssignment:
    id: str
    badge_id: str
    user_id: int  # For consistency with other models, although Zendesk uses string IDs here
    created_at: datetime | None

    @property
    def logical_key(self) -> LogicalKey:
        base = f"id_{self.id}"
        return LogicalKey("badge_assignment", base)
