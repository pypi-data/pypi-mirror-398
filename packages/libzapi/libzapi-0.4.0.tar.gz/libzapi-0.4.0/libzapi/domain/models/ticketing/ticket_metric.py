from dataclasses import dataclass
from datetime import datetime

from libzapi.domain.shared_objects.logical_key import LogicalKey


@dataclass(frozen=True, slots=True)
class TicketMetric:
    id: int
    agent_wait_time_in_minutes: dict
    assigned_at: datetime | None
    assignee_stations: int
    assignee_update_at: datetime | None
    created_at: datetime | None
    custom_status_update_at: datetime
    first_resolution_time_in_minutes: dict
    full_resolution_time_in_minutes: dict
    group_stations: int
    initially_assigned_at: datetime | None
    latest_comment_added_at: datetime | None
    on_hold_time_in_minutes: dict
    reopens: int
    replies: int
    reply_time_in_minutes: dict
    reply_time_in_seconds: dict
    request_updated_at: str
    requester_wait_time_in_minutes: dict
    solved_at: datetime | None
    status_updated_at: datetime | None
    ticket_id: int
    updated_at: datetime | None
    url: str

    @property
    def logical_key(self) -> LogicalKey:
        base = f"metric_{self.id}"
        return LogicalKey("ticket_metric", base)
