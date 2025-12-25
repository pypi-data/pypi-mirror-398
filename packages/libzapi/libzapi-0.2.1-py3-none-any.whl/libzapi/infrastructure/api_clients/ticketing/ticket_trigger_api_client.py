from __future__ import annotations

from typing import Iterator

from libzapi.domain.models.ticketing.ticket_trigger import TicketTrigger
from libzapi.infrastructure.http.client import HttpClient
from libzapi.infrastructure.http.pagination import yield_items
from libzapi.infrastructure.serialization.parse import to_domain


class TicketTriggerApiClient:
    """HTTP adapter for Zendesk Ticket Trigger with shared cursor pagination."""

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def list(self) -> Iterator[TicketTrigger]:
        for obj in yield_items(
            get_json=self._http.get,
            first_path="/api/v2/triggers",
            base_url=self._http.base_url,
            items_key="triggers",
        ):
            yield to_domain(data=obj, cls=TicketTrigger)

    def list_active(self) -> Iterator[TicketTrigger]:
        for obj in yield_items(
            get_json=self._http.get,
            first_path="/api/v2/triggers/active",
            base_url=self._http.base_url,
            items_key="triggers",
        ):
            yield to_domain(data=obj, cls=TicketTrigger)

    def get(self, trigger_id: int) -> TicketTrigger:
        data = self._http.get(f"/api/v2/triggers/{int(trigger_id)}")
        return to_domain(data=data["trigger"], cls=TicketTrigger)
