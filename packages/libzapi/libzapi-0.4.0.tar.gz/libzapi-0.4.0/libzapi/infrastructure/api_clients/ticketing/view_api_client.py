from __future__ import annotations
from typing import Iterable


from libzapi.domain.shared_objects.count_snapshot import CountSnapshot
from libzapi.infrastructure.mappers.count_mapper import to_count_snapshot
from libzapi.infrastructure.http.client import HttpClient
from libzapi.infrastructure.http.pagination import yield_items
from libzapi.infrastructure.serialization.parse import to_domain
from libzapi.domain.models.ticketing.view import View


class ViewApiClient:
    """HTTP adapter for Zendesk Views with shared cursor pagination."""

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def list_all(self) -> Iterable[View]:
        for obj in yield_items(
            get_json=self._http.get,
            first_path="/api/v2/views",
            base_url=self._http.base_url,
            items_key="views",
        ):
            yield to_domain(data=obj, cls=View)

    def list_active(self) -> Iterable[View]:
        for obj in yield_items(
            get_json=self._http.get,
            first_path="/api/v2/views/active",
            base_url=self._http.base_url,
            items_key="views",
        ):
            yield to_domain(data=obj, cls=View)

    def count(self) -> CountSnapshot:
        data = self._http.get("/api/v2/views/count")
        return to_count_snapshot(data["count"])

    def get(self, view_id: int) -> View:
        data = self._http.get(f"/api/v2/views/{int(view_id)}")
        return to_domain(data=data["view"], cls=View)
