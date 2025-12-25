from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CreateSectionCmd:
    parent_section_id: int | None = None
    name: str = ""
    description: str = ""
    locale: str = "en-us"
    position: int = 0


@dataclass(frozen=True, slots=True)
class UpdateSectionCmd:
    category_id: int
    parent_section_id: int
    promote_to_top_level: bool
    name: str = ""
    description: str = ""
    position: int = 0
