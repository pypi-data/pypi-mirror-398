from __future__ import annotations
from typing import Iterable
from libzapi.infrastructure.http.client import HttpClient
from libzapi.infrastructure.http.pagination import yield_items
from libzapi.infrastructure.mappers.ticketing.ticket_field_mapper import to_payload
from libzapi.infrastructure.serialization.parse import to_domain
from libzapi.domain.models.ticketing.ticket_field import TicketField


class TicketFieldApiClient:
    """HTTP adapter for Zendesk Ticket Fields with shared cursor pagination."""

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def list(self) -> Iterable[TicketField]:
        for obj in yield_items(
            get_json=self._http.get,
            first_path="/api/v2/ticket_fields.json",
            base_url=self._http.base_url,
            items_key="ticket_fields",
        ):
            yield to_domain(data=obj, cls=TicketField)

    def get(self, field_id: int) -> TicketField:
        data = self._http.get(f"/api/v2/ticket_fields/{field_id}.json")
        return to_domain(data=data["ticket_field"], cls=TicketField)

    def create(self, entity: TicketField) -> TicketField:
        payload = to_payload(entity)
        data = self._http.post("/api/v2/ticket_fields.json", payload)
        return to_domain(data=data["ticket_field"], cls=TicketField)

    def update(self, field_id: int, entity: TicketField) -> TicketField:
        payload = to_payload(entity)
        data = self._http.put(f"/api/v2/ticket_fields/{field_id}.json", payload)
        return to_domain(data=data["ticket_field"], cls=TicketField)

    def delete(self, field_id: int) -> None:
        self._http.delete(f"/api/v2/ticket_fields/{field_id}.json")
