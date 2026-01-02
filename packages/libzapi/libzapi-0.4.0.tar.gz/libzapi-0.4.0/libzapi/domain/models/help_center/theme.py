from dataclasses import dataclass
from datetime import datetime

from libzapi.domain.shared_objects.logical_key import LogicalKey


@dataclass(frozen=True, slots=True)
class Theme:
    id: str
    brand_id: str
    name: str
    author: str
    live: bool
    created_at: datetime | None
    updated_at: datetime | None
    version: str | None

    @property
    def logical_key(self) -> LogicalKey:
        base = f'v_{self.version}_{self.name.lower().replace(" ", "_")}'
        return LogicalKey("theme", base)
