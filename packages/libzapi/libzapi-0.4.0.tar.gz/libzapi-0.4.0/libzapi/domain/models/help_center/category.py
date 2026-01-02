from dataclasses import dataclass
from datetime import datetime

from libzapi.domain.shared_objects.logical_key import LogicalKey


@dataclass(frozen=True, slots=True)
class Category:
    id: int
    url: str
    html_url: str
    position: int
    name: str
    description: str
    locale: str | None
    source_locale: str | None
    outdated: bool
    created_at: datetime | None
    updated_at: datetime | None

    @property
    def logical_key(self) -> LogicalKey:
        base = self.name.lower().replace(" ", "_")
        return LogicalKey("category", base)
