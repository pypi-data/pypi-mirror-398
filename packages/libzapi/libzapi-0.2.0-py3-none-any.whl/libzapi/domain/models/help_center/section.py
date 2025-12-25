from dataclasses import dataclass
from datetime import datetime

from libzapi.domain.shared_objects.logical_key import LogicalKey


@dataclass(frozen=True, slots=True)
class Section:
    id: int
    url: str
    html_url: str
    category_id: int
    position: int
    sorting: str
    created_at: datetime | None
    updated_at: datetime | None
    name: str
    description: str
    locale: str
    source_locale: str | None
    outdated: bool
    parent_section_id: int | None
    theme_template: str | None

    @property
    def logical_key(self) -> LogicalKey:
        base = self.name.lower().replace(" ", "_")
        return LogicalKey("section", base)
