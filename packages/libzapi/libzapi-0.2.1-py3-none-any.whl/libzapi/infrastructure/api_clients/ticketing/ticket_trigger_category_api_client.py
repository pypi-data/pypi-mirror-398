from __future__ import annotations

from typing import Iterator

from libzapi.domain.models.ticketing.ticket_trigger_category import TicketTriggerCategory
from libzapi.infrastructure.http.client import HttpClient
from libzapi.infrastructure.http.pagination import yield_items
from libzapi.infrastructure.serialization.parse import to_domain


class TicketTriggerCategoryApiClient:
    """HTTP adapter for Zendesk Ticket Trigger Categories with shared cursor pagination."""

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def list(self) -> Iterator[TicketTriggerCategory]:
        for obj in yield_items(
            get_json=self._http.get,
            first_path="/api/v2/trigger_categories",
            base_url=self._http.base_url,
            items_key="trigger_categories",
        ):
            yield to_domain(data=obj, cls=TicketTriggerCategory)

    def get(self, trigger_category_id: int) -> TicketTriggerCategory:
        data = self._http.get(f"/api/v2/trigger_categories/{int(trigger_category_id)}")
        return to_domain(data=data["trigger_category"], cls=TicketTriggerCategory)
