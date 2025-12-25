from typing import Iterable

from libzapi.domain.models.ticketing.ticket_metric_event import MetricEventType
from libzapi.infrastructure.api_clients.ticketing import TicketMetricEventApiClient


class TicketMetricEventsService:
    """High-level service using the API client."""

    def __init__(self, client: TicketMetricEventApiClient) -> None:
        self._client = client

    def list(self, start_time) -> Iterable[type[MetricEventType]]:
        return self._client.list(start_time=start_time)
