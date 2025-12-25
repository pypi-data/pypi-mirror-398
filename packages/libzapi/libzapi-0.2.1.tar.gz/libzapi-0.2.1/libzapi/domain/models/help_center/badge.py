from dataclasses import dataclass
from datetime import datetime

from libzapi.domain.shared_objects.logical_key import LogicalKey


@dataclass(frozen=True, slots=True)
class Badge:
    id: str
    badge_category_id: str
    name: str
    description: str
    icon_url: str
    created_at: datetime | None
    updated_at: datetime | None

    @property
    def logical_key(self) -> LogicalKey:
        base = self.name.lower().replace(" ", "_")
        return LogicalKey("badge", base)
