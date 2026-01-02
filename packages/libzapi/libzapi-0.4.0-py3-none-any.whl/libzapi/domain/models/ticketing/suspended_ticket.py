from dataclasses import dataclass
from datetime import datetime
from typing import List

from libzapi.domain.models.ticketing.attachment import Attachment
from libzapi.domain.shared_objects.logical_key import LogicalKey


@dataclass(frozen=True, slots=True)
class Author:
    id: int
    name: str
    email: str


@dataclass(frozen=True, slots=True)
class User:
    address: str
    name: str


@dataclass(frozen=True, slots=True)
class Source:
    to: User
    from_: User
    rel: str | None


@dataclass(frozen=True, slots=True)
class Via:
    channel: str
    source: Source


@dataclass(frozen=True, slots=True)
class SuspendedTicket:
    id: int
    url: str
    author: Author
    subject: str
    content: str
    cause: str
    cause_id: int
    error_messages: List[str]
    message_id: str
    ticket_id: int
    created_at: datetime
    updated_at: datetime
    via: Via
    attachments: List[Attachment]
    recipient: str
    brand_id: int

    @property
    def logical_key(self) -> LogicalKey:
        base = f"id_{self.id}"
        return LogicalKey("suspended_ticket", base)
