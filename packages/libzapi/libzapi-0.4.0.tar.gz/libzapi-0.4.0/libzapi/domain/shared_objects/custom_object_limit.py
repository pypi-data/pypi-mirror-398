from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CustomObjectLimit:
    count: int
    limit: int
