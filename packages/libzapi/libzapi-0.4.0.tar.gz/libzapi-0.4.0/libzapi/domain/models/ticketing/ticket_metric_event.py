from dataclasses import dataclass
from typing import TypeAlias

from libzapi.domain.shared_objects.logical_key import LogicalKey


@dataclass(frozen=True, slots=True)
class Policy:
    id: str
    title: str
    description: str


@dataclass(frozen=True, slots=True)
class CalendarStatus:
    business: int
    calendar: int


@dataclass(frozen=True, slots=True)
class PolicyMetricTarget:
    target: int
    business_hours: bool
    policy: Policy


@dataclass(frozen=True, slots=True)
class SlaPolicyMetricTarget(PolicyMetricTarget):
    target_in_seconds: int


@dataclass(frozen=True, slots=True)
class TicketMetricEvent:
    id: int
    ticket_id: int
    metric: str
    instance_id: int
    type: str
    time: str
    deleted: bool

    @property
    def logical_key(self) -> LogicalKey:
        base = f"metric_event_id_{self.id}"
        return LogicalKey("ticket_metric_event", base)


@dataclass(frozen=True, slots=True)
class TicketMetricEventUpdateStatus(TicketMetricEvent):
    status: CalendarStatus


@dataclass(frozen=True, slots=True)
class TicketMetricEventSla(TicketMetricEvent):
    sla = SlaPolicyMetricTarget


@dataclass(frozen=True, slots=True)
class TicketMetricEventGroupSla(TicketMetricEvent):
    group_sla: PolicyMetricTarget


MetricEventType: TypeAlias = (
    TicketMetricEventUpdateStatus | TicketMetricEventSla | TicketMetricEventGroupSla | TicketMetricEvent
)
