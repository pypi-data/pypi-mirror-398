from dataclasses import dataclass
from datetime import datetime
from typing import Literal, TypeAlias, Optional, Sequence

from libzapi.domain.shared_objects.logical_key import LogicalKey
from libzapi.domain.shared_objects.relationship import RelationshipFilter


@dataclass(frozen=True, slots=True)
class SystemFieldOption:
    name: str
    value: str


@dataclass(frozen=True, slots=True)
class CustomStatus:
    id: int
    url: str
    status_category: str
    agent_label: str
    end_user_label: str
    description: str
    end_user_description: str
    active: bool
    default: bool
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class CustomFieldOption:
    id: int
    name: str
    raw_name: str
    value: str
    default: bool


CustomFieldType: TypeAlias = Literal[
    "subject",
    "description",
    "status",
    "tickettype",
    "priority",
    "assignee",
    "tagger",
    "group",
    "text",
    "textarea",
    "integer",
    "decimal",
    "date",
    "regexp",
    "checkbox",
    "dropdown",
    "multiselect",
    "lookup",
    "custom_status",
]


@dataclass(frozen=True, slots=True)
class TicketFieldBase:
    url: str
    id: int
    type: str
    title: str
    raw_title: str
    description: str
    raw_description: str
    position: int
    active: bool
    required: bool
    collapsed_for_agents: bool
    regexp_for_validation: str
    title_in_portal: str
    raw_title_in_portal: str
    visible_in_portal: bool
    editable_in_portal: bool
    required_in_portal: bool
    agent_can_edit: bool
    tag: str
    created_at: datetime
    updated_at: datetime
    removable: bool
    agent_description: str

    @property
    def logical_key(self) -> LogicalKey:
        base = self.raw_title.lower().replace(" ", "_")
        return LogicalKey("ticket_field", base)


@dataclass(frozen=True, slots=True)
class CustomFieldText(TicketFieldBase):
    type: Literal["text"]


@dataclass(frozen=True, slots=True)
class CustomFieldTextarea(TicketFieldBase):
    type: Literal["textarea"]


@dataclass(frozen=True, slots=True)
class CustomFieldInteger(TicketFieldBase):
    type: Literal["integer"]


@dataclass(frozen=True, slots=True)
class CustomFieldDecimal(TicketFieldBase):
    type: Literal["decimal"]


@dataclass(frozen=True, slots=True)
class CustomFieldDate(TicketFieldBase):
    type: Literal["date"]


@dataclass(frozen=True, slots=True)
class CustomFieldRegexp(TicketFieldBase):
    type: Literal["regexp"]


@dataclass(frozen=True, slots=True)
class CustomFieldCheckbox(TicketFieldBase):
    type: Literal["checkbox"]
    tag: Optional[str]


@dataclass(frozen=True, slots=True)
class CustomFieldDropdown(TicketFieldBase):
    type: Literal["tagger"]
    custom_field_options: Sequence[CustomFieldOption]


@dataclass(frozen=True, slots=True)
class CustomFieldMultiselect(TicketFieldBase):
    type: Literal["multiselect"]
    custom_field_options: Sequence[CustomFieldOption]


@dataclass(frozen=True, slots=True)
class CustomFieldLookup(TicketFieldBase):
    type: Literal["lookup"]
    relationship_target_type: str
    relationship_filter: Optional[RelationshipFilter] = None


@dataclass(frozen=True, slots=True)
class SystemFieldSubject(TicketFieldBase):
    type: Literal["subject"]


@dataclass(frozen=True, slots=True)
class SystemFieldDescription(TicketFieldBase):
    type: Literal["description"]


@dataclass(frozen=True, slots=True)
class SystemFieldStatus(TicketFieldBase):
    type: Literal["status"]
    system_field_options: Sequence[SystemFieldOption]
    sub_type_id: int


@dataclass(frozen=True, slots=True)
class SystemFieldTicketType(TicketFieldBase):
    type: Literal["tickettype"]
    system_field_options: Sequence[SystemFieldOption]


@dataclass(frozen=True, slots=True)
class SystemFieldPriority(TicketFieldBase):
    type: Literal["priority"]
    system_field_options: Sequence[SystemFieldOption]
    sub_type_id: int


@dataclass(frozen=True, slots=True)
class SystemFieldBasicPriority(TicketFieldBase):
    type: Literal["basic_priority"]
    system_field_options: Sequence[SystemFieldOption]
    sub_type_id: int


@dataclass(frozen=True, slots=True)
class SystemFieldGroup(TicketFieldBase):
    type: Literal["group"]


@dataclass(frozen=True, slots=True)
class SystemFieldAssignee(TicketFieldBase):
    type: Literal["assignee"]


@dataclass(frozen=True, slots=True)
class SystemFieldCustomStatus(TicketFieldBase):
    type: Literal["custom_status"]
    custom_statuses: Sequence[CustomStatus]


TicketField: TypeAlias = (
    CustomFieldText
    | CustomFieldTextarea
    | CustomFieldInteger
    | CustomFieldDecimal
    | CustomFieldDate
    | CustomFieldRegexp
    | CustomFieldCheckbox
    | CustomFieldDropdown
    | CustomFieldMultiselect
    | CustomFieldLookup
    | SystemFieldSubject
    | SystemFieldDescription
    | SystemFieldStatus
    | SystemFieldCustomStatus
    | SystemFieldTicketType
    | SystemFieldPriority
    | SystemFieldBasicPriority
    | SystemFieldGroup
    | SystemFieldAssignee
)
