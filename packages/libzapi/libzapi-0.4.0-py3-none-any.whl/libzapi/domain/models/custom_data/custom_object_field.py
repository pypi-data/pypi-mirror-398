from dataclasses import dataclass
from datetime import datetime
from typing import Optional, TypeAlias, Literal, Sequence

from libzapi.domain.shared_objects.logical_key import LogicalKey
from libzapi.domain.shared_objects.relationship import RelationshipFilter


@dataclass(frozen=True, slots=True)
class CustomFieldOption:
    id: int
    name: str
    raw_name: str
    value: str


CustomObjectFieldType: TypeAlias = Literal[
    "text",
    "textarea",
    "integer",
    "decimal",
    "date",
    "regexp",
    "checkbox",
    "dropdown",
    "multiselect",
    "lookup",
]


@dataclass(frozen=True, slots=True)
class CustomObjectFieldBase:
    url: str
    id: int
    type: CustomObjectFieldType
    key: str
    title: str
    description: str
    raw_title: str
    raw_description: str
    position: int
    active: bool
    system: bool
    regexp_for_validation: Optional[str]
    created_at: datetime
    updated_at: datetime

    @property
    def logical_key(self) -> LogicalKey:
        base = self.key.lower().replace(" ", "_")
        return LogicalKey("custom_object_field", base)


# ---- Variants by type -------------------------------------------------------


@dataclass(frozen=True, slots=True)
class CustomObjectFieldText(CustomObjectFieldBase):
    type: Literal["text"]


@dataclass(frozen=True, slots=True)
class CustomObjectFieldTextarea(CustomObjectFieldBase):
    type: Literal["textarea"]


@dataclass(frozen=True, slots=True)
class CustomObjectFieldInteger(CustomObjectFieldBase):
    type: Literal["integer"]


@dataclass(frozen=True, slots=True)
class CustomObjectFieldDecimal(CustomObjectFieldBase):
    type: Literal["decimal"]


@dataclass(frozen=True, slots=True)
class CustomObjectFieldDate(CustomObjectFieldBase):
    type: Literal["date"]


@dataclass(frozen=True, slots=True)
class CustomObjectFieldRegexp(CustomObjectFieldBase):
    type: Literal["regexp"]


@dataclass(frozen=True, slots=True)
class CustomObjectFieldCheckbox(CustomObjectFieldBase):
    type: Literal["checkbox"]
    tag: Optional[str]


@dataclass(frozen=True, slots=True)
class CustomObjectFieldDropdown(CustomObjectFieldBase):
    type: Literal["dropdown"]
    custom_field_options: Sequence[CustomFieldOption]


@dataclass(frozen=True, slots=True)
class CustomObjectFieldMultiselect(CustomObjectFieldBase):
    type: Literal["multiselect"]
    custom_field_options: Sequence[CustomFieldOption]


@dataclass(frozen=True, slots=True)
class CustomObjectFieldLookup(CustomObjectFieldBase):
    type: Literal["lookup"]
    relationship_target_type: str
    relationship_filter: RelationshipFilter


CustomObjectField: TypeAlias = (
    CustomObjectFieldText
    | CustomObjectFieldTextarea
    | CustomObjectFieldInteger
    | CustomObjectFieldDecimal
    | CustomObjectFieldDate
    | CustomObjectFieldRegexp
    | CustomObjectFieldCheckbox
    | CustomObjectFieldDropdown
    | CustomObjectFieldMultiselect
    | CustomObjectFieldLookup
)
