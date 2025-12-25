from dataclasses import dataclass
from datetime import datetime

from libzapi.domain.shared_objects.logical_key import LogicalKey


@dataclass(frozen=True, slots=True)
class Translation:
    id: int
    url: str
    html_url: str
    source_id: int
    source_type: str
    locale: str
    title: str
    body: str
    outdated: bool
    draft: bool
    hidden: bool
    created_at: datetime | None
    updated_at: datetime | None
    updated_by_id: int | None
    created_by_id: int | None

    @property
    def logical_key(self) -> LogicalKey:
        base = self.title.lower().replace(" ", "_")
        return LogicalKey("translation", base)
