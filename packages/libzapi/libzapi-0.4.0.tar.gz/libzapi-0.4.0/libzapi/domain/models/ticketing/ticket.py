from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from libzapi.domain.shared_objects.logical_key import LogicalKey


@dataclass(frozen=True, slots=True)
class Source:
    to: dict
    from_: dict
    rel: Optional[str]


@dataclass(frozen=True, slots=True)
class Via:
    channel: str
    source: Source


@dataclass(frozen=True, slots=True)
class CustomField:
    id: int
    value: Optional[str]


@dataclass(frozen=True, slots=True)
class SatisfactionRating:
    score: str


@dataclass(frozen=True, slots=True)
class User:
    id: int
    name: str


@dataclass(frozen=True, slots=True)
class Ticket:
    id: int
    url: str
    external_id: str
    via: Via
    created_at: datetime
    updated_at: datetime
    generated_timestamp: int
    type: Optional[str]
    subject: str
    raw_subject: str
    description: str
    priority: Optional[str]
    status: str
    recipient: Optional[str]
    requester_id: int
    submitter_id: int
    assignee_id: Optional[int]
    organization_id: Optional[int]
    group_id: Optional[int]
    collaborator_ids: List[int]
    follower_ids: List[int]
    email_cc_ids: List[int]
    forum_topic_id: Optional[int]
    problem_id: Optional[int]
    has_incidents: bool
    is_public: bool
    due_at: Optional[datetime]
    tags: List[str]
    custom_fields: List[CustomField]
    satisfaction_rating: Optional[SatisfactionRating]
    sharing_agreement_ids: List[int]
    custom_status_id: Optional[int]
    encoded_id: str
    fields: List[CustomField]
    followup_ids: List[int]
    ticket_form_id: Optional[int]
    brand_id: Optional[int]
    allow_channelback: bool
    allow_attachments: bool
    from_messaging_channel: bool
    support_type: Optional[str]

    @property
    def logical_key(self) -> LogicalKey:
        base = f"{self.id}"
        return LogicalKey("ticket", base)
