from dataclasses import dataclass
from typing import TypeAlias, Literal, Sequence

LookupOperator: TypeAlias = Literal[
    "is",
    "is_not",
    "includes",
    "not_includes",
    "present",
    "less_than",
    "less_than_equal",
    "greater_than",
    "greater_than_equal",
]


@dataclass(frozen=True, slots=True)
class RelationshipFilterClause:
    field: str
    operator: LookupOperator
    value: str


@dataclass(frozen=True, slots=True)
class RelationshipFilter:
    all: Sequence[RelationshipFilterClause] = ()
    any: Sequence[RelationshipFilterClause] = ()
