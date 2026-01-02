from typing import Iterable

from libzapi.domain.models.ticketing.user import User
from libzapi.domain.shared_objects.count_snapshot import CountSnapshot
from libzapi.infrastructure.api_clients.ticketing.user_api_client import UserApiClient


class UsersService:
    """High-level service using the API client."""

    def __init__(self, client: UserApiClient) -> None:
        self._client = client

    def list_all(self) -> Iterable[User]:
        return self._client.list_all()

    def list_by_group(self, group_id: int) -> Iterable[User]:
        return self._client.list_by_group(group_id)

    def list_by_organization(self, organization_id: int) -> Iterable[User]:
        return self._client.list_by_organization(organization_id)

    def count(self) -> CountSnapshot:
        return self._client.count()

    def count_by_group(self, group_id: int) -> CountSnapshot:
        return self._client.count_by_group(group_id)

    def count_by_organization(self, organization_id: int) -> CountSnapshot:
        return self._client.count_by_organization(organization_id)

    def get_by_id(self, user_id: int) -> User:
        return self._client.get(user_id)
