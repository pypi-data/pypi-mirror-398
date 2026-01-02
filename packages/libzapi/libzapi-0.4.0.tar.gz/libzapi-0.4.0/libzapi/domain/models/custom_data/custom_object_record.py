from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from libzapi.domain.shared_objects.logical_key import LogicalKey
from libzapi.domain.shared_objects.thumbnail import Thumbnail


@dataclass(frozen=True, slots=True)
class CustomObjectRecord:
    url: str
    id: str
    name: str
    custom_object_key: str
    custom_object_fields: dict[str, str]
    created_by_user_id: str
    updated_by_user_id: str
    created_at: datetime
    updated_at: datetime
    external_id: str | None
    photo: Optional[Thumbnail]

    @property
    def logical_key(self) -> LogicalKey:
        base = self.id.lower().replace(" ", "_")
        return LogicalKey("custom_object_record", base)
