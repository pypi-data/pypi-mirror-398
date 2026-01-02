from typing import Iterable

from libzapi.domain.models.ticketing.ticket_metric import TicketMetric
from libzapi.infrastructure.api_clients.ticketing.ticket_metric_api_client import TicketMetricApiClient


class TicketMetricsService:
    """High-level service using the API client."""

    def __init__(self, client: TicketMetricApiClient) -> None:
        self._client = client

    def list_by_ticket(self, ticket_id) -> Iterable[TicketMetric]:
        return self._client.list_ticket(ticket_id)

    def get_by_id(self, ticket_metric_id: int) -> TicketMetric:
        return self._client.get(ticket_metric_id)
