from dataclasses import dataclass
from datetime import datetime

from libzapi.domain.shared_objects.logical_key import LogicalKey


@dataclass(frozen=True, slots=True)
class Topic:
    id: int
    url: str
    html_url: str
    name: str
    description: str | None
    position: int
    follower_count: int
    community_id: int
    created_at: datetime | None
    updated_at: datetime | None
    manageable_by: str | None
    user_segment_id: int | None

    @property
    def logical_key(self) -> LogicalKey:
        base = self.name.lower().replace(" ", "_")
        return LogicalKey("topic", base)
