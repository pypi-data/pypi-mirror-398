from dataclasses import dataclass
from datetime import datetime
from typing import List

from libzapi.domain.shared_objects.logical_key import LogicalKey


@dataclass(frozen=True, slots=True)
class PostComment:
    id: int
    body: str
    author_id: int
    vote_sum: int | None
    vote_count: int | None
    official: bool | None
    html_url: str
    created_at: datetime | None
    updated_at: datetime | None
    url: str
    post_id: int
    non_author_editor_id: List[str] | None
    non_author_updated_at: datetime | None

    @property
    def logical_key(self) -> LogicalKey:
        base = f"id_{self.id}"
        return LogicalKey("post_comment", base)
