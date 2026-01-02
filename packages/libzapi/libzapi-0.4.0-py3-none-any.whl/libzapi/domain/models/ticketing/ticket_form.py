from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from libzapi.domain.shared_objects.logical_key import LogicalKey


@dataclass(frozen=True, slots=True)
class RequiredOnStatus:
    type: str


@dataclass(frozen=True, slots=True)
class ChildField:
    id: int
    is_required: bool
    required_on_statuses: Optional[RequiredOnStatus] = None


@dataclass(frozen=True, slots=True)
class Condition:
    parent_field_id: int
    parent_field_type: str
    value: str
    child_fields: list[ChildField] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class TicketForm:
    id: int
    raw_name: str
    raw_display_name: str
    end_user_visible: bool
    position: int
    ticket_field_ids: list[int]
    active: bool
    default: bool
    in_all_brands: bool
    restricted_brand_ids: list[int]
    url: str
    name: str
    display_name: str
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None
    end_user_conditions: Optional[list[Condition]] = field(default_factory=list)
    agent_conditions: Optional[list[Condition]] = field(default_factory=list)

    @property
    def logical_key(self) -> LogicalKey:
        base = self.raw_name.lower().replace(" ", "_")
        return LogicalKey("ticket_form", base)
