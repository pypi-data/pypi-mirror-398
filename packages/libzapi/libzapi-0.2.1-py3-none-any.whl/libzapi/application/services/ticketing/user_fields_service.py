from typing import Iterable

from libzapi.domain.models.ticketing.user_field import UserField, CustomFieldOption
from libzapi.infrastructure.api_clients.ticketing.user_field_api_client import UserFieldApiClient


class UserFieldsService:
    """High-level service using the API client."""

    def __init__(self, client: UserFieldApiClient) -> None:
        self._client = client

    def list_all(self) -> Iterable[UserField]:
        return self._client.list_all()

    def list_options(self, user_field_id: int) -> Iterable[CustomFieldOption]:
        return self._client.list_options(user_field_id=user_field_id)

    def get_by_id(self, user_field_id: int) -> UserField:
        return self._client.get(user_field_id=user_field_id)

    def get_option_by_id(self, user_field_id: int, user_field_option_id: int) -> CustomFieldOption:
        return self._client.get_option(user_field_id=user_field_id, user_field_option_id=user_field_option_id)
