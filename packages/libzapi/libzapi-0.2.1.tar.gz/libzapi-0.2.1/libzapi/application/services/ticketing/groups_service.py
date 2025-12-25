from typing import Iterable

from libzapi.application.commands.ticketing.group_cmds import CreateGroupCmd, UpdateGroupCmd
from libzapi.domain.shared_objects.count_snapshot import CountSnapshot
from libzapi.domain.models.ticketing.group import Group
from libzapi.infrastructure.api_clients.ticketing.group_api_client import GroupApiClient


class GroupsService:
    """High-level service using the API client."""

    def __init__(self, client: GroupApiClient) -> None:
        self._client = client

    def list_all(self) -> Iterable[Group]:
        return self._client.list()

    def list_user(self, user_id: int) -> Iterable[Group]:
        return self._client.list_user(user_id)

    def list_assignable(self) -> Iterable[Group]:
        return self._client.list_assignable()

    def count(self) -> CountSnapshot:
        return self._client.count()

    def count_user(self, user_id: int) -> CountSnapshot:
        return self._client.count_user(user_id)

    def get_by_id(self, group_id: int) -> Group:
        return self._client.get(group_id)

    def create(self, entity: CreateGroupCmd) -> Group:
        return self._client.create(entity)

    def update(self, group_id: int, entity: UpdateGroupCmd) -> Group:
        return self._client.update(group_id, entity)

    def delete(self, group_id: int) -> None:
        self._client.delete(group_id)
