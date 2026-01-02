from dataclasses import dataclass
from datetime import datetime

from libzapi.domain.shared_objects.logical_key import LogicalKey


@dataclass(frozen=True, slots=True)
class ArticleAttachment:
    id: int
    url: str
    article_id: int
    display_file_name: str
    file_name: str
    locale: str | None
    content_url: str
    relative_path: str
    content_type: str
    size: int
    inline: bool
    created_at: datetime | None
    updated_at: datetime | None

    @property
    def logical_key(self) -> LogicalKey:
        base = self.file_name.lower().replace(" ", "_")
        return LogicalKey("article_attachment", base)
