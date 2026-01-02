from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from libzapi.domain.shared_objects.condition import AllAnyCondition
from libzapi.domain.shared_objects.logical_key import LogicalKey


@dataclass(frozen=True, slots=True)
class CustomFieldOption:
    id: int
    name: str
    raw_name: str
    value: str
    position: Optional[int] = None


@dataclass(frozen=True, slots=True)
class UserField:
    id: int
    url: str
    type: str
    key: str
    title: str
    description: str
    raw_description: str
    position: int
    active: bool
    system: bool
    regexp_for_validation: Optional[str]
    created_at: datetime | None
    updated_at: datetime | None
    relationship_target_type: Optional[str] = None
    relationship_filter: Optional[AllAnyCondition] = None
    custom_field_options: Optional[list[CustomFieldOption]] = field(default_factory=list)

    @property
    def logical_key(self) -> LogicalKey:
        base = self.key.lower().replace(" ", "_")
        return LogicalKey("user_field", base)
