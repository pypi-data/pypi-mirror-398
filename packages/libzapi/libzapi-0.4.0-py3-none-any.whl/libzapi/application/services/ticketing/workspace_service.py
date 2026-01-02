from typing import Iterable

from libzapi.domain.models.ticketing.workspace import Workspace
from libzapi.infrastructure.api_clients.ticketing.workspace_api_client import WorkspaceApiClient


class WorkspaceService:
    """High-level service using the API client."""

    def __init__(self, client: WorkspaceApiClient) -> None:
        self._client = client

    def list(self) -> Iterable[Workspace]:
        return self._client.list()

    def get(self, workspace_id: int) -> Workspace:
        return self._client.get(workspace_id)
