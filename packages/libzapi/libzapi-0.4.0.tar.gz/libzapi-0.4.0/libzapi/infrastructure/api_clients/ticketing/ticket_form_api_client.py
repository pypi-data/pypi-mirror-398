from __future__ import annotations
from typing import Iterable

from libzapi.domain.models.ticketing.ticket_form import TicketForm
from libzapi.infrastructure.http.client import HttpClient
from libzapi.infrastructure.http.pagination import yield_items
from libzapi.infrastructure.serialization.parse import to_domain


class TicketFormApiClient:
    """HTTP adapter for Zendesk Groups with shared cursor pagination."""

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def list(self) -> Iterable[TicketForm]:
        for obj in yield_items(
            get_json=self._http.get,
            first_path="/api/v2/ticket_forms",
            base_url=self._http.base_url,
            items_key="ticket_forms",
        ):
            yield to_domain(data=obj, cls=TicketForm)

    def get(self, ticket_form_id: int) -> TicketForm:
        data = self._http.get(f"/api/v2/ticket_forms/{int(ticket_form_id)}")
        return to_domain(data=data["ticket_form"], cls=TicketForm)
