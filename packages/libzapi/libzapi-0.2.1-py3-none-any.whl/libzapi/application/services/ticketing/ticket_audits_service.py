from typing import Iterable

from libzapi.domain.models.ticketing.ticket_audit import TicketAudit
from libzapi.infrastructure.api_clients.ticketing.ticket_audit_api_client import TicketAuditApiClient


class TicketAuditsService:
    """High-level service using the API client."""

    def __init__(self, client: TicketAuditApiClient) -> None:
        self._client = client

    def list_by_ticket(self, user_id) -> Iterable[TicketAudit]:
        return self._client.list_ticket(user_id)

    def get_by_id(self, audit_id, ticket_id: int) -> TicketAudit:
        return self._client.get(audit_id, ticket_id)
