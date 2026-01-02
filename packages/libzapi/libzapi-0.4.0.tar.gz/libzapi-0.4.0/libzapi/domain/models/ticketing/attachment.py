from dataclasses import dataclass
from typing import List

from libzapi.domain.shared_objects.logical_key import LogicalKey
from libzapi.domain.shared_objects.thumbnail import AttachmentThumbnail


@dataclass(frozen=True, slots=True)
class Attachment:
    id: int
    url: str
    file_name: str
    content_url: str
    mapped_content_url: str
    content_type: str
    size: int
    width: int
    height: int
    inline: bool
    deleted: bool
    malware_access_override: bool
    malware_scan_result: str
    thumbnails: List[AttachmentThumbnail]

    @property
    def logical_key(self) -> LogicalKey:
        base = self.file_name.lower().replace(" ", "_")
        return LogicalKey("attachment", base)
