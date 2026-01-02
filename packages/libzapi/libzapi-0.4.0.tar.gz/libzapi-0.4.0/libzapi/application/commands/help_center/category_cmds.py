from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CreateCategoryCmd:
    name: str = ""
    description: str = ""
    locale: str = "en-us"
    position: int = 0


@dataclass(frozen=True, slots=True)
class UpdateCategoryCmd:
    name: str = ""
    description: str = ""
    position: int = 0
