from typing import Iterable

from libzapi.domain.models.ticketing.automation import Automation
from libzapi.infrastructure.api_clients.ticketing import AutomationApiClient


class AutomationsService:
    """High-level service using the API client."""

    def __init__(self, client: AutomationApiClient) -> None:
        self._client = client

    def list_all(self) -> Iterable[Automation]:
        return self._client.list_all()

    def list_active(self) -> Iterable[Automation]:
        return self._client.list_active()

    def get(self, automation_id: int) -> Automation:
        return self._client.get(automation_id=automation_id)
