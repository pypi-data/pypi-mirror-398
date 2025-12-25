from typing import Iterable

from libzapi.domain.models.ticketing.ticket_form import TicketForm
from libzapi.infrastructure.api_clients.ticketing.ticket_form_api_client import TicketFormApiClient


class TicketFormsService:
    """High-level service using the API client."""

    def __init__(self, client: TicketFormApiClient) -> None:
        self._client = client

    def list_all(self) -> Iterable[TicketForm]:
        return self._client.list()

    def get_by_id(self, ticket_form_id: int) -> TicketForm:
        return self._client.get(ticket_form_id)
