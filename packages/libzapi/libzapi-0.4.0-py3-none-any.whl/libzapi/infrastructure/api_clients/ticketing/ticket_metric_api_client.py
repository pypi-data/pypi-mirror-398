from __future__ import annotations

from typing import Iterable

from libzapi.domain.models.ticketing.ticket_metric import TicketMetric
from libzapi.infrastructure.http.client import HttpClient
from libzapi.infrastructure.http.pagination import yield_items
from libzapi.infrastructure.serialization.parse import to_domain


class TicketMetricApiClient:
    """HTTP adapter for Zendesk Groups with shared cursor pagination."""

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def list_ticket(self, ticket_id: int) -> Iterable[TicketMetric]:
        for obj in yield_items(
            get_json=self._http.get,
            first_path=f"/api/v2/tickets/{int(ticket_id)}/metrics",
            base_url=self._http.base_url,
            items_key="ticket_metrics",
        ):
            yield to_domain(data=obj, cls=TicketMetric)

    def get(self, ticket_metric_id: int) -> TicketMetric:
        data = self._http.get(f"/api/v2/ticket_metrics/{int(ticket_metric_id)}")
        return to_domain(data=data["ticket_metric"], cls=TicketMetric)
