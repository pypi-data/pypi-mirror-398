from typing import Iterable
from libzapi.domain.models.ticketing.ticket_field import TicketField
from libzapi.infrastructure.api_clients.ticketing.ticket_field_api_client import TicketFieldApiClient


class TicketFieldsService:
    """High-level service using the API client."""

    def __init__(self, client: TicketFieldApiClient) -> None:
        self._client = client

    def list_all(self) -> Iterable[TicketField]:
        return self._client.list()

    def get_by_id(self, field_id: int) -> TicketField:
        return self._client.get(field_id)

    def create_field(self, entity: TicketField) -> TicketField:
        return self._client.create(entity)

    def update_field(self, field_id: int, entity: TicketField) -> TicketField:
        return self._client.update(field_id, entity)

    def delete_field(self, field_id: int) -> None:
        self._client.delete(field_id)
