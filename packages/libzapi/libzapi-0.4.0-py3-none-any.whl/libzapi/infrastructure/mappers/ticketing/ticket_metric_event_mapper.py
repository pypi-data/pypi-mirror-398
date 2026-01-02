from libzapi.domain.models.ticketing.ticket_metric_event import (
    TicketMetricEventUpdateStatus,
    TicketMetricEventSla,
    TicketMetricEventGroupSla,
    TicketMetricEvent,
    MetricEventType,
)
from libzapi.infrastructure.serialization.parse import to_domain as parse_domain


def event_switcher(data: dict) -> type[MetricEventType]:
    """Switch between different TicketMetricEvent subclasses based on the 'type' field in the data."""
    switcher = {
        "update_status": TicketMetricEventUpdateStatus,
        "apply_sla": TicketMetricEventSla,
        "apply_group_sla": TicketMetricEventGroupSla,
    }
    cls = switcher.get(data.get("type"), TicketMetricEvent)
    return cls


def to_domain(data: dict) -> type[MetricEventType]:
    """Convert a dict or JSON-like structure into a domain entity."""
    cls = event_switcher(data)
    data = parse_domain(data, cls)
    return data
