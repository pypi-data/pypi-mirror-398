from dataclasses import dataclass
from datetime import datetime

from libzapi.domain.shared_objects.logical_key import LogicalKey


@dataclass(frozen=True, slots=True)
class CustomObject:
    url: str
    key: str
    created_by_user_id: int
    updated_by_user_id: int
    created_at: datetime
    updated_at: datetime
    title: str
    raw_title: str
    title_pluralized: str
    raw_title_pluralized: str
    description: str
    raw_description: str
    include_in_list_view: bool
    allows_photos: bool
    allows_attachments: bool

    @property
    def logical_key(self) -> LogicalKey:
        base = self.key.lower().replace(" ", "_")
        return LogicalKey("custom_object", base)
