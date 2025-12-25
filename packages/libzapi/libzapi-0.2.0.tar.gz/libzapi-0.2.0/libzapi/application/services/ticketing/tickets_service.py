from typing import Iterable

from libzapi.domain.models.ticketing.ticket import Ticket, User
from libzapi.domain.shared_objects.count_snapshot import CountSnapshot
from libzapi.infrastructure.api_clients.ticketing.ticket_api_client import TicketApiClient


class TickestService:
    """High-level service using the API client."""

    def __init__(self, client: TicketApiClient) -> None:
        self._client = client

    def list(self) -> Iterable[Ticket]:
        return self._client.list()

    def list_organization(self, organization_id: int) -> Iterable[Ticket]:
        return self._client.list_organization(organization_id=organization_id)

    def list_user_requested(self, user_id: int) -> Iterable[Ticket]:
        return self._client.list_user_requested(user_id=user_id)

    def list_user_ccd(self, user_id: int) -> Iterable[Ticket]:
        return self._client.list_user_ccd(user_id=user_id)

    def list_user_followed(self, user_id: int) -> Iterable[Ticket]:
        return self._client.list_user_followed(user_id=user_id)

    def list_user_assigned(self, user_id: int) -> Iterable[Ticket]:
        return self._client.list_user_assigned(user_id=user_id)

    def list_recent(self) -> Iterable[Ticket]:
        return self._client.list_recent()

    def list_collaborators(self, ticket_id: int) -> Iterable[User]:
        return self._client.list_collaborators(ticket_id=ticket_id)

    def list_followers(self, ticket_id: int) -> Iterable[User]:
        return self._client.list_followers(ticket_id=ticket_id)

    def list_email_ccs(self, ticket_id: int) -> Iterable[User]:
        return self._client.list_email_ccs(ticket_id=ticket_id)

    def list_incidents(self, ticket_id: int) -> Iterable[Ticket]:
        return self._client.list_incidents(ticket_id=ticket_id)

    def list_problems(self) -> Iterable[Ticket]:
        return self._client.list_problems()

    def get(self, ticket_id: int) -> Ticket:
        return self._client.get(ticket_id=ticket_id)

    def count(self) -> CountSnapshot:
        return self._client.count()

    def organization_count(self, organization_id: int) -> CountSnapshot:
        return self._client.organization_count(organization_id=organization_id)

    def user_ccd_count(self, user_id: int) -> CountSnapshot:
        return self._client.user_ccd_count(user_id=user_id)

    def user_assigned_count(self, user_id: int) -> CountSnapshot:
        return self._client.user_assigned_count(user_id=user_id)

    def show_multiple_tickets(self, ticket_ids: Iterable[int]) -> Iterable[Ticket]:
        return self._client.show_multiple_tickets(ticket_ids=ticket_ids)
