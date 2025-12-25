from dataclasses import dataclass
from datetime import datetime
from typing import List

from libzapi.domain.shared_objects.logical_key import LogicalKey


@dataclass(frozen=True, slots=True)
class PermissionGroup:
    id: int
    name: str
    built_in: bool
    publish: List[int]
    created_at: datetime | None
    updated_at: datetime | None
    edit: List[int]

    @property
    def logical_key(self) -> LogicalKey:
        base = self.name.lower().replace(" ", "_")
        return LogicalKey("permission_group", base)
