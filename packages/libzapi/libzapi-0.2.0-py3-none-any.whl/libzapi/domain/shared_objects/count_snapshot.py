from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CountSnapshot:
    refreshed_at: str
    value: int
