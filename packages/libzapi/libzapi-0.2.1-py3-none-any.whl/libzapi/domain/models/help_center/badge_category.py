from dataclasses import dataclass
from datetime import datetime

from libzapi.domain.shared_objects.logical_key import LogicalKey


@dataclass(frozen=True, slots=True)
class BadgeCategory:
    id: int
    brand_id: int  # For consistency with other models, although Zendesk uses string IDs here
    name: str
    slug: str
    created_at: datetime | None
    updated_at: datetime | None

    @property
    def logical_key(self) -> LogicalKey:
        base = self.name.lower().replace(" ", "_")
        return LogicalKey("badge_category", base)
