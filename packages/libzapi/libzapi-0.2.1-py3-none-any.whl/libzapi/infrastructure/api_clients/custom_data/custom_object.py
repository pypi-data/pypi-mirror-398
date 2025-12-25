from typing import Iterator

from libzapi.domain.models.custom_data.custom_object import CustomObject
from libzapi.domain.shared_objects.custom_object_limit import CustomObjectLimit
from libzapi.infrastructure.http.client import HttpClient
from libzapi.infrastructure.http.pagination import yield_items
from libzapi.infrastructure.serialization.parse import to_domain


class CustomObjectApiClient:
    """HTTP adapter for Zendesk Custom Objects"""

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def list_all(self) -> Iterator[CustomObject]:
        for obj in yield_items(
            get_json=self._http.get,
            first_path="/api/v2/custom_objects",
            base_url=self._http.base_url,
            items_key="custom_objects",
        ):
            yield to_domain(data=obj, cls=CustomObject)

    def get(self, custom_object_id: str) -> CustomObject:
        data = self._http.get(f"/api/v2/custom_objects/{custom_object_id}")
        return to_domain(data=data["custom_object"], cls=CustomObject)

    def create(self, payload: dict) -> CustomObject:
        raise NotImplementedError

    def update(self, custom_object_id: str, data: dict) -> CustomObject:
        raise NotImplementedError

    def delete(self, custom_object_id: str) -> CustomObject:
        raise NotImplementedError

    def limit(self) -> CustomObjectLimit:
        data = self._http.get("/api/v2/custom_objects/limits/object_limit")
        return to_domain(data=data, cls=CustomObjectLimit)
