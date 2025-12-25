from __future__ import annotations

from typing import Iterable

from libzapi.domain.models.ticketing.workspace import Workspace
from libzapi.infrastructure.http.client import HttpClient
from libzapi.infrastructure.http.pagination import yield_items
from libzapi.infrastructure.serialization.parse import to_domain


class WorkspaceApiClient:
    """HTTP adapter for Zendesk Workspace"""

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def list(self) -> Iterable[Workspace]:
        for obj in yield_items(
            get_json=self._http.get,
            first_path="/api/v2/workspaces",
            base_url=self._http.base_url,
            items_key="workspaces",
        ):
            yield to_domain(data=obj, cls=Workspace)

    def get(self, workspace_id: int) -> Workspace:
        data = self._http.get(f"/api/v2/workspaces/{int(workspace_id)}")
        return to_domain(data=data["workspace"], cls=Workspace)
