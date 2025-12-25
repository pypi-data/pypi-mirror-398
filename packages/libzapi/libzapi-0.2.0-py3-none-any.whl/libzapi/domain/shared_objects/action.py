from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Action:
    field: str
    value: str
