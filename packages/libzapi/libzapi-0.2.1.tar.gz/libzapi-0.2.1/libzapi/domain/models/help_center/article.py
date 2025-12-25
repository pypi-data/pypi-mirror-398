from dataclasses import dataclass
from datetime import datetime

from libzapi.domain.shared_objects.logical_key import LogicalKey


@dataclass(frozen=True, slots=True)
class Article:
    id: int
    url: str
    html_url: str
    author_id: int
    comments_disabled: bool
    draft: bool
    promote: bool
    position: int
    vote_sum: int
    vote_count: int
    section_id: int
    created_at: datetime
    updated_at: datetime
    name: str
    title: str
    source_locale: str
    locale: str
    outdated: bool
    outdated_locales: list[str]
    edited_at: datetime | None
    user_segment_id: int | None
    permission_group_id: int | None
    content_tag_ids: list[str]
    label_names: list[str]
    body: str | None
    user_segment_ids: list[int] | None

    @property
    def logical_key(self) -> LogicalKey:
        base = self.title.lower().replace(" ", "_")
        return LogicalKey("article", base)
