from dataclasses import dataclass
from datetime import datetime

from libzapi.domain.shared_objects.condition import AllAnyCondition
from libzapi.domain.shared_objects.logical_key import LogicalKey


@dataclass(frozen=True, slots=True)
class App:
    id: int
    expand: bool
    position: int


@dataclass(frozen=True, slots=True)
class SelectedMacro:
    id: int
    title: str
    active: bool
    usage_7d: int
    restriction: dict | None


@dataclass(frozen=True, slots=True)
class Workspace:
    id: int
    url: str
    title: str
    description: str
    macro_ids: list[int]
    ticket_form_id: int | None
    layout_uuid: str | None
    apps: list[App]
    position: int
    activated: bool
    conditions: AllAnyCondition
    updated_at: datetime
    created_at: datetime
    knowledge_settings: dict
    selected_macros: list[SelectedMacro]

    @property
    def logical_key(self) -> LogicalKey:
        base = self.title.lower().replace(" ", "_")
        return LogicalKey("workspace", base)
