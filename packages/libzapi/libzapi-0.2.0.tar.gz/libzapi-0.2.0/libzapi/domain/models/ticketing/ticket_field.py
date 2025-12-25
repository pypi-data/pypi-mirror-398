from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

from libzapi.domain.shared_objects.logical_key import LogicalKey


@dataclass(frozen=True, slots=True)
class TicketField:
    id: int
    active: bool
    agent_can_edit: bool
    agent_description: str
    collapsed_for_agents: bool
    created_at: datetime
    creator_app_name: str
    creator_user_id: str
    custom_field_options: Iterable[dict]
    custom_statuses: Iterable[dict]
    description: str
    editable_in_portal: bool
    position: int
    raw_description: str
    raw_title: str
    raw_title_in_portal: str
    regexp_for_validation: str
    relationship_filter: dict
    relationship_target_type: str
    removable: bool
    required: bool
    required_in_portal: bool
    sub_type_id: int
    system_field_options: Iterable[dict]
    tag: str
    title: str
    title_in_portal: str
    type: str
    updated_at: datetime
    url: str

    @property
    def logical_key(self) -> LogicalKey:
        base = self.raw_title.lower().replace(" ", "_")
        return LogicalKey("ticket_field", base)
