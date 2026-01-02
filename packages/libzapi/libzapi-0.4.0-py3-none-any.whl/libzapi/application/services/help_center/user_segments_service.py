from typing import Iterable

from libzapi.application.commands.help_center.user_segments_cmds import (
    CreateUserSegmentCmd,
    UpdateUserSegmentCmd,
    UserType,
)
from libzapi.domain.models.help_center.section import Section
from libzapi.domain.models.help_center.topic import Topic
from libzapi.domain.models.help_center.user_segment import UserSegment
from libzapi.infrastructure.api_clients.help_center import UserSegmentApiClient


class UserSegmentsService:
    """High-level service using the API client."""

    def __init__(self, client: UserSegmentApiClient) -> None:
        self._client = client

    def list_all(self) -> Iterable[UserSegment]:
        return self._client.list_all()

    def list_applicable(self) -> Iterable[UserSegment]:
        return self._client.list_applicable()

    def list_segments_by_user(self, user_id: int) -> Iterable[UserSegment]:
        return self._client.list_user(user_id=user_id)

    def list_topics_by_segment(self, user_segment_id: int) -> Iterable[Topic]:
        return self._client.list_topics(user_segment_id=user_segment_id)

    def list_sections_by_segment(self, user_segment_id: int) -> Iterable[Section]:
        return self._client.list_sections(user_segment_id=user_segment_id)

    def get(self, user_segment_id: int) -> UserSegment:
        return self._client.get(user_segment_id=user_segment_id)

    def create(
        self,
        name: str,
        user_type: str,
        tags: list[str] | None = None,
        or_tags: list[str] | None = None,
        added_user_ids: list[int] | None = None,
        groups_ids: list[int] | None = None,
        organization_ids: list[int] | None = None,
    ) -> UserSegment:
        cmd = CreateUserSegmentCmd(
            name=name,
            user_type=UserType(user_type),
            tags=tags,
            or_tags=or_tags,
            added_user_ids=added_user_ids,
            groups_ids=groups_ids,
            organization_ids=organization_ids,
        )
        return self._client.create(cmd=cmd)

    def update(
        self,
        user_segment_id: int,
        name: str,
        user_type: str,
        tags: list[str] | None = None,
        or_tags: list[str] | None = None,
        added_user_ids: list[int] | None = None,
        groups_ids: list[int] | None = None,
        organization_ids: list[int] | None = None,
    ) -> UserSegment:
        cmd = UpdateUserSegmentCmd(
            name=name,
            user_type=UserType(user_type),
            tags=tags,
            or_tags=or_tags,
            added_user_ids=added_user_ids,
            groups_ids=groups_ids,
            organization_ids=organization_ids,
        )

        return self._client.update(user_segment_id=user_segment_id, cmd=cmd)

    def delete(self, user_segment_id: int) -> None:
        self._client.delete(user_segment_id=user_segment_id)
