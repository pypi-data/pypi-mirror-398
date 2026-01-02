from dataclasses import dataclass
from datetime import datetime

from libzapi.domain.shared_objects.logical_key import LogicalKey


@dataclass(frozen=True, slots=True)
class Group:
    id: int
    default: bool
    deleted: bool
    description: str
    is_public: bool
    name: str
    url: str
    created_at: datetime
    updated_at: datetime

    @property
    def logical_key(self) -> LogicalKey:
        base = self.name.lower().replace(" ", "_")
        return LogicalKey("group", base)
