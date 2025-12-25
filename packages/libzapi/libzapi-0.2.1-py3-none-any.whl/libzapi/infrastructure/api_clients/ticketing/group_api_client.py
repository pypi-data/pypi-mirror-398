from __future__ import annotations
from typing import Iterable

from libzapi.application.commands.ticketing.group_cmds import CreateGroupCmd, UpdateGroupCmd
from libzapi.domain.shared_objects.count_snapshot import CountSnapshot
from libzapi.infrastructure.mappers.count_mapper import to_count_snapshot
from libzapi.infrastructure.http.client import HttpClient
from libzapi.infrastructure.http.pagination import yield_items
from libzapi.infrastructure.mappers.ticketing.group_mapper import to_payload_create, to_payload_update
from libzapi.infrastructure.serialization.parse import to_domain
from libzapi.domain.models.ticketing.group import Group


class GroupApiClient:
    """HTTP adapter for Zendesk Groups with shared cursor pagination."""

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def list(self) -> Iterable[Group]:
        for obj in yield_items(
            get_json=self._http.get,
            first_path="/api/v2/groups",
            base_url=self._http.base_url,
            items_key="groups",
        ):
            yield to_domain(data=obj, cls=Group)

    def list_user(self, user_id: int) -> Iterable[Group]:
        for obj in yield_items(
            get_json=self._http.get,
            first_path=f"/api/v2/users/{int(user_id)}/groups",
            base_url=self._http.base_url,
            items_key="groups",
        ):
            yield to_domain(data=obj, cls=Group)

    def count(self) -> CountSnapshot:
        data = self._http.get("/api/v2/groups/count")
        return to_count_snapshot(data["count"])

    def count_user(self, user_id: int) -> CountSnapshot:
        data = self._http.get(f"/api/v2/users/{int(user_id)}/groups/count")
        return to_count_snapshot(data["count"])

    def list_assignable(self) -> Iterable[Group]:
        for obj in yield_items(
            get_json=self._http.get,
            first_path="/api/v2/groups/assignable",
            base_url=self._http.base_url,
            items_key="groups",
        ):
            yield to_domain(data=obj, cls=Group)

    def get(self, group_id: int) -> Group:
        data = self._http.get(f"/api/v2/groups/{int(group_id)}")
        return to_domain(data=data["group"], cls=Group)

    def create(self, entity: CreateGroupCmd) -> Group:
        payload = to_payload_create(entity)
        data = self._http.post("/api/v2/groups", payload)
        return to_domain(data=data["group"], cls=Group)

    def update(self, group_id: int, entity: UpdateGroupCmd) -> Group:
        payload = to_payload_update(entity)
        data = self._http.put(f"/api/v2/groups/{int(group_id)}", payload)
        return to_domain(data=data["group"], cls=Group)

    def delete(self, group_id: int) -> None:
        self._http.delete(f"/api/v2/groups/{int(group_id)}")
