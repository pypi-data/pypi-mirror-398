from typing import Iterable

from libzapi.domain.models.ticketing.suspended_ticket import SuspendedTicket
from libzapi.infrastructure.api_clients.ticketing import SuspendedTicketApiClient


class SuspendedTicketsService:
    """High-level service using the API client."""

    def __init__(self, client: SuspendedTicketApiClient) -> None:
        self._client = client

    def list_all(self) -> Iterable[SuspendedTicket]:
        return self._client.list()

    def get_by_id(self, id_: int) -> SuspendedTicket:
        return self._client.get(id_)
