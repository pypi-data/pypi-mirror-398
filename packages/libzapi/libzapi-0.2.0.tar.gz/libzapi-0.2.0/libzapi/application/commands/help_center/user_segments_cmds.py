"""User Segments Commands"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True, slots=True)
class UserType:
    value: str

    _allowed = {"signed_in_users", "staff"}

    def __post_init__(self):
        if self.value not in self._allowed:
            raise ValueError("user_type must be 'signed_in_users' or 'staff'")

    def __str__(self):
        return self.value


@dataclass(frozen=True, slots=True)
class BaseUserSegmentCmd:
    name: str
    user_type: UserType
    tags: Optional[list[str]] = None
    or_tags: Optional[list[str]] = None
    added_user_ids: Optional[list[int]] = None
    groups_ids: Optional[list[int]] = None
    organization_ids: Optional[list[int]] = None


@dataclass(frozen=True, slots=True)
class CreateUserSegmentCmd(BaseUserSegmentCmd): ...


@dataclass(frozen=True, slots=True)
class UpdateUserSegmentCmd(BaseUserSegmentCmd): ...
