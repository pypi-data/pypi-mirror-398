from dataclasses import dataclass
from datetime import datetime

from libzapi.domain.shared_objects.logical_key import LogicalKey


@dataclass(frozen=True, slots=True)
class UserSegment:
    id: int
    user_type: str
    group_ids: list[int]
    organization_ids: list[int]
    tags: list[str]
    or_tags: list[str]
    created_at: datetime | None
    updated_at: datetime | None
    built_in: bool
    added_user_ids: list[int]
    name: str

    @property
    def logical_key(self) -> LogicalKey:
        base = self.name.lower().replace(" ", "_")
        return LogicalKey("user_segment", base)
