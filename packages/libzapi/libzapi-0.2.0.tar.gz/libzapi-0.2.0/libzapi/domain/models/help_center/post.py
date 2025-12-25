from dataclasses import dataclass
from datetime import datetime
from typing import List

from libzapi.domain.shared_objects.logical_key import LogicalKey


@dataclass(frozen=True, slots=True)
class Post:
    id: int
    title: str
    details: str
    author_id: int
    vote_sum: int
    vote_count: int
    comment_count: int
    follower_count: int
    topic_id: int
    html_url: str
    created_at: datetime | None
    updated_at: datetime | None
    url: str
    featured: bool
    pinned: bool
    closed: bool
    frozen: bool
    status: str
    non_author_edit_id: List[int] | None
    non_author_updated_at: datetime | None
    content_tag_ids: List[str] | None

    @property
    def logical_key(self) -> LogicalKey:
        base = self.title.lower().replace(" ", "_")
        return LogicalKey("post", base)
