from dataclasses import dataclass
from datetime import datetime, date
from libzapi.domain.shared_objects.logical_key import LogicalKey


@dataclass(frozen=True, slots=True)
class Schedule:
    id: int
    intervals: list[dict]
    name: str
    time_zone: str
    created_at: datetime
    updated_at: datetime

    @property
    def logical_key(self) -> LogicalKey:
        base = self.name.lower().replace(" ", "_")
        return LogicalKey("schedule", base)


@dataclass(frozen=True, slots=True)
class Holiday:
    id: int
    name: str
    start_date: date
    end_date: date

    @property
    def logical_key(self) -> LogicalKey:
        base = self.name.lower().replace(" ", "_")
        return LogicalKey("schedule_holiday", base)
