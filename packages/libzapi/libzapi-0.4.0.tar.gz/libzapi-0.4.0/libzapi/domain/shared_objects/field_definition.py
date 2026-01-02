from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FieldDefinition:
    id: int
    title: str
    type: str
    url: str
    filterable: bool
    sortable: bool
    order: str


@dataclass(frozen=True, slots=True)
class ShortFieldDefinition:
    id: int
    title: str
    filterable: str
    sortable: str
