from typing import Iterator

from libzapi.domain.models.custom_data.custom_object import CustomObject
from libzapi.domain.shared_objects.custom_object_limit import CustomObjectLimit
from libzapi.infrastructure.api_clients.custom_data import CustomObjectApiClient


class CustomObjectsService:
    """High-level service using the API client."""

    def __init__(self, client: CustomObjectApiClient) -> None:
        self._client = client

    def list_all(self) -> Iterator[CustomObject]:
        return self._client.list_all()

    def get(self, custom_object_id: str) -> CustomObject:
        return self._client.get(custom_object_id=custom_object_id)

    def limit(self) -> CustomObjectLimit:
        return self._client.limit()
