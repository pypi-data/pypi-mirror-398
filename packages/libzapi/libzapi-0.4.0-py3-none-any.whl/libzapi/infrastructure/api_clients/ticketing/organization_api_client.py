from __future__ import annotations

from typing import Iterator, Optional

from libzapi.domain.models.ticketing.organization import Organization
from libzapi.domain.shared_objects.count_snapshot import CountSnapshot
from libzapi.infrastructure.http.client import HttpClient
from libzapi.infrastructure.http.pagination import yield_items
from libzapi.infrastructure.mappers.count_mapper import to_count_snapshot
from libzapi.infrastructure.serialization.parse import to_domain


class OrganizationApiClient:
    """HTTP adapter for Zendesk Organizations"""

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def list(self) -> Iterator[Organization]:
        for obj in yield_items(
            get_json=self._http.get,
            first_path="/api/v2/organizations",
            base_url=self._http.base_url,
            items_key="organizations",
        ):
            yield to_domain(data=obj, cls=Organization)

    def list_organizations(self, user_id: int) -> Iterator[Organization]:
        for obj in yield_items(
            get_json=self._http.get,
            first_path=f"/api/v2/users/{user_id}/organizations",
            base_url=self._http.base_url,
            items_key="organizations",
        ):
            yield to_domain(data=obj, cls=Organization)

    def get(self, organization_id: int) -> Organization:
        data = self._http.get(f"/api/v2/organizations/{int(organization_id)}")
        return to_domain(data=data["organization"], cls=Organization)

    def search(self, external_id: Optional[str] = None, name: Optional[str] = None) -> Iterator[Organization]:
        if not external_id and not name:
            raise ValueError("Either external_id or name must be provided for search.")
        if external_id:
            search_term = "external_id"
            search_value = external_id
        else:
            search_term = "name"
            search_value = name
        data = self._http.get(f"/api/v2/organizations/search?{search_term}={search_value}")
        for obj in data.get("organizations", []) or []:
            yield to_domain(data=obj, cls=Organization)

    def count(self) -> CountSnapshot:
        data = self._http.get("/api/v2/organizations/count")
        return to_count_snapshot(data["count"])
