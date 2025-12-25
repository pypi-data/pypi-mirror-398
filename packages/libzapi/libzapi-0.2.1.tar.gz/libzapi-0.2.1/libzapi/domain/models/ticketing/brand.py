from dataclasses import dataclass
from datetime import datetime
from typing import List

from libzapi.domain.shared_objects.logical_key import LogicalKey
from libzapi.domain.shared_objects.thumbnail import Thumbnail


@dataclass(frozen=True, slots=True)
class Logo:
    url: str
    id: int
    file_name: str
    content_url: str
    mapped_content_url: str
    content_type: str
    size: int
    width: int
    height: int
    inline: bool
    deleted: bool
    thumbnails: List[Thumbnail]


@dataclass(frozen=True, slots=True)
class Brand:
    id: int
    url: str
    name: str
    subdomain: str
    host_mapping: str | None
    has_help_center: bool
    help_center_state: str
    active: bool
    default: bool
    is_deleted: bool
    logo: Logo
    ticket_form_ids: List[int]
    signature_template: str
    created_at: datetime
    updated_at: datetime

    @property
    def logical_key(self) -> LogicalKey:
        base = self.name.lower().replace(" ", "_")
        return LogicalKey("brand", base)
