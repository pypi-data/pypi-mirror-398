from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

from libzapi.domain.shared_objects.via import Via
from libzapi.domain.shared_objects.logical_key import LogicalKey


@dataclass(frozen=True, slots=True)
class Request:
    id: int
    assignee_id: int
    can_be_solved_by_me: bool
    collaborator_ids: Iterable[int]
    created_at: datetime
    custom_fields: Iterable[dict]
    custom_status_id: int
    description: str
    due_at: datetime
    email_cc_ids: Iterable[int]
    followup_source_id: int | None
    group_id: int
    is_public: bool
    organization_id: int | None
    priority: str
    recipient: str | None
    requester_id: int
    solved: bool
    status: str
    subject: str
    ticket_form_id: int | None
    type: str | None
    updated_at: datetime
    url: str
    via: Via

    @property
    def logical_key(self) -> LogicalKey:
        base = f"request_{self.id}"
        return LogicalKey("request", base)
