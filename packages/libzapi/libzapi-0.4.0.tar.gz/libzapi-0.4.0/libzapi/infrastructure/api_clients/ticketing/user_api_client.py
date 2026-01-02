from __future__ import annotations
from typing import Iterable

from libzapi.domain.shared_objects.count_snapshot import CountSnapshot
from libzapi.infrastructure.mappers.count_mapper import to_count_snapshot
from libzapi.infrastructure.http.client import HttpClient
from libzapi.infrastructure.http.pagination import yield_items
from libzapi.infrastructure.serialization.parse import to_domain
from libzapi.domain.models.ticketing.user import User


class UserApiClient:
    """HTTP adapter for Zendesk Users with shared cursor pagination."""

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def list_all(self) -> Iterable[User]:
        for obj in yield_items(
            get_json=self._http.get,
            first_path="/api/v2/users",
            base_url=self._http.base_url,
            items_key="users",
        ):
            yield to_domain(data=obj, cls=User)

    def list_by_group(self, group_id) -> Iterable[User]:
        for obj in yield_items(
            get_json=self._http.get,
            first_path=f"/api/v2/groups/{group_id}/users",
            base_url=self._http.base_url,
            items_key="users",
        ):
            yield to_domain(data=obj, cls=User)

    def list_by_organization(self, organization_id) -> Iterable[User]:
        for obj in yield_items(
            get_json=self._http.get,
            first_path=f"/api/v2/organizations/{organization_id}/users",
            base_url=self._http.base_url,
            items_key="users",
        ):
            yield to_domain(data=obj, cls=User)

    def count(self) -> CountSnapshot:
        data = self._http.get("/api/v2/users/count")
        return to_count_snapshot(data["count"])

    def count_by_group(self, group_id) -> CountSnapshot:
        data = self._http.get(f"/api/v2/groups/{group_id}/users/count")
        return to_count_snapshot(data["count"])

    def count_by_organization(self, organization_id) -> CountSnapshot:
        data = self._http.get(f"/api/v2/organizations/{organization_id}/users/count")
        return to_count_snapshot(data["count"])

    def get(self, user_id: int) -> User:
        data = self._http.get(f"/api/v2/users/{int(user_id)}")
        return to_domain(data=data["user"], cls=User)
