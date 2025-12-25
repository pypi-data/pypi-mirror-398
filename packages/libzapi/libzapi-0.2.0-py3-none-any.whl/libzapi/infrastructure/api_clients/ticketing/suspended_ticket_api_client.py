from __future__ import annotations

from typing import Iterable

from libzapi.domain.models.ticketing.suspended_ticket import SuspendedTicket
from libzapi.infrastructure.http.client import HttpClient
from libzapi.infrastructure.http.pagination import yield_items
from libzapi.infrastructure.serialization.parse import to_domain


class SuspendedTicketApiClient:
    """HTTP adapter for Zendesk Suspended Tickets with shared cursor pagination."""

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def list(self) -> Iterable[SuspendedTicket]:
        for obj in yield_items(
            get_json=self._http.get,
            first_path="/api/v2/suspended_tickets",
            base_url=self._http.base_url,
            items_key="suspended_tickets",
        ):
            yield to_domain(data=obj, cls=SuspendedTicket)

    def get(self, id_: int) -> SuspendedTicket:
        data = self._http.get(f"/api/v2/suspended_tickets/{int(id_)}")
        return to_domain(data=data["suspended_ticket"], cls=SuspendedTicket)
