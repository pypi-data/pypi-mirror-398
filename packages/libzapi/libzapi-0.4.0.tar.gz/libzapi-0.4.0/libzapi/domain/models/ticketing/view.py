from dataclasses import dataclass
from datetime import datetime

from libzapi.domain.shared_objects.condition import AllAnyCondition
from libzapi.domain.shared_objects.field_definition import FieldDefinition, ShortFieldDefinition
from libzapi.domain.shared_objects.logical_key import LogicalKey


@dataclass(frozen=True, slots=True)
class Execution:
    group_by: int | None
    group_order: str
    sort_by: str
    sort_order: str | None
    group: FieldDefinition | None
    sort: FieldDefinition | None
    columns: list[FieldDefinition] | None
    fields: list[ShortFieldDefinition] | None
    custom_fields: list[FieldDefinition] | None


@dataclass(frozen=True, slots=True)
class View:
    id: int
    url: str
    title: str
    active: bool
    updated_at: datetime
    created_at: datetime
    default: bool
    position: int
    description: str
    execution: Execution
    conditions: list[AllAnyCondition] | None
    restriction: dict
    raw_title: str

    @property
    def logical_key(self) -> LogicalKey:
        base = self.raw_title.lower().replace(" ", "_")
        return LogicalKey("view", base)
