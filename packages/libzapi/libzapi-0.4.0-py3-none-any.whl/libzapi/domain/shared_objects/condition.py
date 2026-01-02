from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class Condition:
    field: str
    operator: str
    value: str


@dataclass(frozen=True, slots=True)
class AllAnyCondition:
    all: list[Condition] = field(default_factory=list)
    any: list[Condition] = field(default_factory=list)
