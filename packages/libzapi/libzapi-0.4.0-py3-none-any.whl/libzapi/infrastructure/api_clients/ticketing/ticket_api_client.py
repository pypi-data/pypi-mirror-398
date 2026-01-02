from __future__ import annotations

from typing import Iterator, Iterable

from libzapi.domain.models.ticketing.ticket import Ticket, User
from libzapi.domain.shared_objects.count_snapshot import CountSnapshot
from libzapi.domain.shared_objects.job_status import JobStatus
from libzapi.infrastructure.http.client import HttpClient
from libzapi.infrastructure.http.pagination import yield_items
from libzapi.infrastructure.serialization.parse import to_domain
from libzapi.infrastructure.mappers.ticketing.ticket_mapper import to_payload_create, to_payload_update
from libzapi.application.commands.ticketing.ticket_cmds import CreateTicketCmd, UpdateTicketCmd


class TicketApiClient:
    """HTTP adapter for Zendesk Tickets"""

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def list(self) -> Iterator[Ticket]:
        data = self._http.get("/api/v2/tickets")
        for obj in data["tickets"]:
            yield to_domain(data=obj, cls=Ticket)

    def list_organization(self, organization_id: int) -> Iterator[Ticket]:
        return self._list_tickets(path=f"/api/v2/organizations/{int(organization_id)}/tickets")

    def list_user_requested(self, user_id: int) -> Iterator[Ticket]:
        return self._list_tickets(path=f"/api/v2/users/{int(user_id)}/tickets/requested")

    def list_user_ccd(self, user_id: int) -> Iterator[Ticket]:
        return self._list_tickets(path=f"/api/v2/users/{int(user_id)}/tickets/ccd")

    def list_user_followed(self, user_id: int) -> Iterator[Ticket]:
        return self._list_tickets(path=f"/api/v2/users/{int(user_id)}/tickets/followed")

    def list_user_assigned(self, user_id: int) -> Iterator[Ticket]:
        return self._list_tickets(path=f"/api/v2/users/{int(user_id)}/tickets/assigned")

    def list_recent(self) -> Iterator[Ticket]:
        return self._list_tickets(path="/api/v2/tickets/recent")

    def list_collaborators(self, ticket_id: int) -> Iterator[User]:
        data = self._http.get(f"/api/v2/tickets/{int(ticket_id)}/collaborators")
        for obj in data["users"]:
            yield to_domain(data=obj, cls=User)

    def list_followers(self, ticket_id: int) -> Iterator[User]:
        data = self._http.get(f"/api/v2/tickets/{int(ticket_id)}/followers")
        for obj in data["users"]:
            yield to_domain(data=obj, cls=User)

    def list_email_ccs(self, ticket_id: int) -> Iterator[User]:
        data = self._http.get(f"/api/v2/tickets/{int(ticket_id)}/email_ccs")
        for obj in data["users"]:
            yield to_domain(data=obj, cls=User)

    def list_incidents(self, ticket_id: int) -> Iterator[Ticket]:
        return self._list_tickets(path=f"/api/v2/tickets/{int(ticket_id)}/incidents")

    def list_problems(self) -> Iterator[Ticket]:
        return self._list_tickets(path="/api/v2/tickets/problems")

    def get(self, ticket_id: int) -> Ticket:
        data = self._http.get(f"/api/v2/tickets/{int(ticket_id)}")
        return to_domain(data=data["ticket"], cls=Ticket)

    def count(self) -> CountSnapshot:
        data = self._http.get("/api/v2/tickets/count")
        return data["count"]

    def organization_count(self, organization_id: int) -> CountSnapshot:
        data = self._http.get(f"/api/v2/organizations/{int(organization_id)}/tickets/count")
        return data["count"]

    def user_ccd_count(self, user_id: int) -> CountSnapshot:
        data = self._http.get(f"/api/v2/users/{int(user_id)}/tickets/ccd/count")
        return data["count"]

    def user_assigned_count(self, user_id: int) -> CountSnapshot:
        data = self._http.get(f"/api/v2/users/{int(user_id)}/tickets/assigned/count")
        return data["count"]

    def show_multiple_tickets(self, ticket_ids: Iterable[int]) -> Iterator[Ticket]:
        ids_str = ",".join(str(id_) for id_ in ticket_ids)
        data = self._http.get(f"/api/v2/tickets/show_many?ids={ids_str}")
        for obj in data["tickets"]:
            yield to_domain(data=obj, cls=Ticket)

    def create_ticket(self, entity: CreateTicketCmd) -> Ticket:
        payload = to_payload_create(entity)
        data = self._http.post("/api/v2/tickets", payload)
        return to_domain(data=data["ticket"], cls=Ticket)

    def update_ticket(self, ticket_id: int, entity: UpdateTicketCmd) -> Ticket:
        payload = to_payload_update(entity)
        data = self._http.put(f"/api/v2/tickets/{int(ticket_id)}", payload)
        return to_domain(data=data["ticket"], cls=Ticket)

    def create_many(self, entity: Iterable[CreateTicketCmd]) -> JobStatus:
        payload = {"tickets": [to_payload_create(e)["ticket"] for e in entity]}
        data = self._http.post("/api/v2/tickets/create_many", payload)
        return to_domain(data=data["job_status"], cls=JobStatus)

    def _list_tickets(self, path: str) -> Iterator[Ticket]:
        """Helper to reduce code duplication for listing tickets."""
        items = yield_items(
            get_json=self._http.get,
            first_path=path,
            base_url=self._http.base_url,
            items_key="tickets",
        )
        return (to_domain(data=obj, cls=Ticket) for obj in items)
