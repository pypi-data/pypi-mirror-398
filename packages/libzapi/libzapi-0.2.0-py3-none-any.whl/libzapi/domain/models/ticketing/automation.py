from dataclasses import dataclass
from datetime import datetime
from typing import List

from libzapi.domain.shared_objects.action import Action
from libzapi.domain.shared_objects.condition import AllAnyCondition
from libzapi.domain.shared_objects.logical_key import LogicalKey


@dataclass(frozen=True, slots=True)
class Automation:
    id: int
    url: str
    title: str
    active: bool
    updated_at: datetime
    created_at: datetime
    default: bool
    actions: List[Action]
    conditions: AllAnyCondition
    position: int
    raw_title: str

    @property
    def logical_key(self) -> LogicalKey:
        base = self.raw_title.lower().replace(" ", "_")
        return LogicalKey("automation", base)
