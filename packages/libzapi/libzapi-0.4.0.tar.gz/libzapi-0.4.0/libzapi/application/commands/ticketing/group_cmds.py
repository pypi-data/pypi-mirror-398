from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CreateGroupCmd:
    name: str
    description: str = ""
    is_public: bool = False
    default: bool = False


@dataclass(frozen=True, slots=True)
class UpdateGroupCmd:
    # partial update intent
    name: str | None = None
    description: str | None = None
    is_public: bool | None = None
    default: bool | None = None
