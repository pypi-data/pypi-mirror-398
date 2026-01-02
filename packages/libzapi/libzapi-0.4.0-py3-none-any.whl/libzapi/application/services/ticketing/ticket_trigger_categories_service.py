from typing import Iterable

from libzapi.domain.models.ticketing.ticket_trigger_category import TicketTriggerCategory
from libzapi.infrastructure.api_clients.ticketing.ticket_trigger_category_api_client import TicketTriggerCategoryApiClient


class TicketTriggerCategoriesService:
    """High-level service using the API client."""

    def __init__(self, client: TicketTriggerCategoryApiClient) -> None:
        self._client = client

    def list(self) -> Iterable[TicketTriggerCategory]:
        return self._client.list()

    def get(self, trigger_category_id: int) -> TicketTriggerCategory:
        return self._client.get(trigger_category_id=trigger_category_id)
