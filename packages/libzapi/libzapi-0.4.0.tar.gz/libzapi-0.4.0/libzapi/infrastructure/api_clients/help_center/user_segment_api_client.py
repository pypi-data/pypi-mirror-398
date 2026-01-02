from __future__ import annotations

from typing import Iterator

from libzapi.application.commands.help_center.user_segments_cmds import CreateUserSegmentCmd, UpdateUserSegmentCmd
from libzapi.domain.models.help_center.user_segment import UserSegment
from libzapi.domain.models.help_center.section import Section
from libzapi.domain.models.help_center.topic import Topic
from libzapi.infrastructure.http.client import HttpClient
from libzapi.infrastructure.http.pagination import yield_items
from libzapi.infrastructure.mappers.help_center.user_segment_mapper import (
    to_payload_create,
    to_payload_update,
)
from libzapi.infrastructure.serialization.parse import to_domain


class UserSegmentApiClient:
    """HTTP adapter for Zendesk User Segment in Help Center"""

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def list_all(self) -> Iterator[UserSegment]:
        for obj in yield_items(
            get_json=self._http.get,
            first_path="/api/v2/help_center/user_segments",
            base_url=self._http.base_url,
            items_key="user_segments",
        ):
            yield to_domain(data=obj, cls=UserSegment)

    def list_applicable(self) -> Iterator[UserSegment]:
        for obj in yield_items(
            get_json=self._http.get,
            first_path="/api/v2/help_center/user_segments/applicable",
            base_url=self._http.base_url,
            items_key="user_segments",
        ):
            yield to_domain(data=obj, cls=UserSegment)

    def list_user(self, user_id: int) -> Iterator[UserSegment]:
        for obj in yield_items(
            get_json=self._http.get,
            first_path=f"/api/v2/help_center/users/{int(user_id)}/user_segments",
            base_url=self._http.base_url,
            items_key="user_segments",
        ):
            yield to_domain(data=obj, cls=UserSegment)

    def list_sections(self, user_segment_id: int) -> Iterator[Section]:
        for obj in yield_items(
            get_json=self._http.get,
            first_path=f"/api/v2/help_center/user_segments/{int(user_segment_id)}/sections",
            base_url=self._http.base_url,
            items_key="sections",
        ):
            yield to_domain(data=obj, cls=Section)

    def list_topics(self, user_segment_id: int) -> Iterator[Topic]:
        for obj in yield_items(
            get_json=self._http.get,
            first_path=f"/api/v2/help_center/user_segments/{int(user_segment_id)}/topics",
            base_url=self._http.base_url,
            items_key="topics",
        ):
            yield to_domain(data=obj, cls=Topic)

    def get(self, user_segment_id: int) -> UserSegment:
        data = self._http.get(f"/api/v2/help_center/user_segments/{user_segment_id}")
        return to_domain(data=data["user_segment"], cls=UserSegment)

    def create(self, cmd: CreateUserSegmentCmd) -> UserSegment:
        payload = to_payload_create(cmd)
        data = self._http.post("/api/v2/help_center/user_segments", json=payload)
        return to_domain(data=data["user_segment"], cls=UserSegment)

    def update(self, user_segment_id: int, cmd: UpdateUserSegmentCmd) -> UserSegment:
        payload = to_payload_update(cmd)
        data = self._http.put(f"/api/v2/help_center/user_segments/{int(user_segment_id)}", json=payload)
        return to_domain(data=data["user_segment"], cls=UserSegment)

    def delete(self, user_segment_id: int) -> None:
        self._http.delete(f"/api/v2/help_center/user_segments/{int(user_segment_id)}")
