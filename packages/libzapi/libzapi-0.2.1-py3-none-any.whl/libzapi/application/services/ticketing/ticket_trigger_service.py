from typing import Iterable

from libzapi.domain.models.ticketing.ticket_trigger import TicketTrigger
from libzapi.infrastructure.api_clients.ticketing import TicketTriggerApiClient


class TicketTriggerService:
    """High-level service using the API client."""

    def __init__(self, client: TicketTriggerApiClient) -> None:
        self._client = client

    def list(self) -> Iterable[TicketTrigger]:
        return self._client.list()

    def list_active(self) -> Iterable[TicketTrigger]:
        return self._client.list_active()

    def get(self, trigger_id: int) -> TicketTrigger:
        return self._client.get(trigger_id=trigger_id)
