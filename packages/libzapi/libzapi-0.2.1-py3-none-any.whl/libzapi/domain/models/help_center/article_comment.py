from dataclasses import dataclass
from datetime import datetime

from libzapi.domain.shared_objects.logical_key import LogicalKey


@dataclass(frozen=True, slots=True)
class ArticleComment:
    id: int
    url: str
    body: str
    author_id: int
    source_id: int
    source_type: str
    html_url: str
    locale: str | None
    created_at: datetime | None
    updated_at: datetime | None
    vote_sum: int | None
    vote_count: int | None
    non_author_editor_id: int | None
    non_author_updated_at: datetime | None

    @property
    def logical_key(self) -> LogicalKey:
        base = f"id_{self.id}"
        return LogicalKey("article_comment", base)
