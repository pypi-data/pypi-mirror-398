from __future__ import annotations

from typing import Iterable

from libzapi.domain.models.ticketing.ticket_audit import TicketAudit
from libzapi.infrastructure.http.client import HttpClient
from libzapi.infrastructure.http.pagination import yield_items
from libzapi.infrastructure.serialization.parse import to_domain


class TicketAuditApiClient:
    """HTTP adapter for Zendesk Groups with shared cursor pagination."""

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def list_ticket(self, ticket_id: int) -> Iterable[TicketAudit]:
        for obj in yield_items(
            get_json=self._http.get,
            first_path=f"/api/v2/tickets/{int(ticket_id)}/audits",
            base_url=self._http.base_url,
            items_key="ticket_audits",
        ):
            yield to_domain(data=obj, cls=TicketAudit)

    def get(self, ticket_audit_id: int, ticket_id: int) -> TicketAudit:
        data = self._http.get(f"/api/v2/tickets/{int(ticket_id)}/{ticket_audit_id}")
        return to_domain(data=data["ticket_audit"], cls=TicketAudit)
