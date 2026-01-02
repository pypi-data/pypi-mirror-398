from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from libzapi.domain.shared_objects.action import Action
from libzapi.domain.shared_objects.logical_key import LogicalKey


@dataclass(frozen=True, slots=True)
class Restriction:
    type: str
    id: int
    ids: list[int]


@dataclass(frozen=True, slots=True)
class Macro:
    id: int
    url: str
    title: str
    active: bool
    updated_at: datetime
    created_at: datetime
    default: bool
    position: int
    description: str
    actions: list[Action]
    raw_title: str
    restriction: Optional[Restriction] = None

    @property
    def logical_key(self) -> LogicalKey:
        base = self.raw_title.lower().replace(" ", "_")
        return LogicalKey("macro", base)
