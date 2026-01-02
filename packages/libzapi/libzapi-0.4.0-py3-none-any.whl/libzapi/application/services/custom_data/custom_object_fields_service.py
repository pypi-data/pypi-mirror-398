from typing import Iterator

from libzapi.domain.models.custom_data.custom_object_field import CustomObjectField
from libzapi.infrastructure.api_clients.custom_data import CustomObjectFieldApiClient


class CustomObjectFieldsService:
    """High-level service using the API client."""

    def __init__(self, client: CustomObjectFieldApiClient) -> None:
        self._client = client

    def list_all(self, custom_object_key: str) -> Iterator[CustomObjectField]:
        return self._client.list_all(custom_object_key)

    def get(self, custom_object_key: str, custom_object_field_id: int) -> CustomObjectField:
        return self._client.get(custom_object_key=custom_object_key, custom_object_field_id=custom_object_field_id)
