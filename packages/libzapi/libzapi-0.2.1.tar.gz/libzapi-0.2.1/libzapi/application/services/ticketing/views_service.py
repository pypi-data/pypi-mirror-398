from typing import Iterable

from libzapi.domain.models.ticketing.view import View
from libzapi.domain.shared_objects.count_snapshot import CountSnapshot
from libzapi.infrastructure.api_clients.ticketing.view_api_client import ViewApiClient


class ViewsService:
    """High-level service using the API client."""

    def __init__(self, client: ViewApiClient) -> None:
        self._client = client

    def list_all(self) -> Iterable[View]:
        return self._client.list_all()

    def list_active(self, view_id: int) -> View:
        return self._client.get(view_id=view_id)

    def count(self) -> CountSnapshot:
        return self._client.count()

    def get_by_id(self, view_id: int) -> View:
        return self._client.get(view_id)
