from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Thumbnail:
    url: str
    id: str
    file_name: str
    content_url: str
    mapped_content_url: str
    content_type: str
    size: int
    width: int
    height: int
    inline: bool
    deleted: bool


@dataclass(frozen=True, slots=True)
class AttachmentThumbnail(Thumbnail):
    malware_access_override: bool
    malware_scan_result: str
