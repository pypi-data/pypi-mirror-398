from __future__ import annotations

from typing import Iterator

from libzapi.domain.models.ticketing.ticket_metric_event import MetricEventType
from libzapi.infrastructure.http.client import HttpClient
from libzapi.infrastructure.http.pagination import yield_items
from libzapi.infrastructure.mappers.ticketing.ticket_metric_event_mapper import to_domain


class TicketMetricEventApiClient:
    """HTTP adapter for Zendesk Ticket Metric Events with shared cursor pagination."""

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def list(self, start_time: int) -> Iterator[type[MetricEventType]]:
        for obj in yield_items(
            get_json=self._http.get,
            first_path=f"/api/v2/incremental/ticket_metric_events?start_time={start_time}",
            base_url=self._http.base_url,
            items_key="ticket_metric_events",
        ):
            yield to_domain(data=obj)
