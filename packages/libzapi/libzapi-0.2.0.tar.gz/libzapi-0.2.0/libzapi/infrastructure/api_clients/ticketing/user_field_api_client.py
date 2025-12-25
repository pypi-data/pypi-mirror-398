from __future__ import annotations
from typing import Iterable


from libzapi.infrastructure.http.client import HttpClient
from libzapi.infrastructure.http.pagination import yield_items
from libzapi.infrastructure.serialization.parse import to_domain
from libzapi.domain.models.ticketing.user_field import UserField, CustomFieldOption


class UserFieldApiClient:
    """HTTP adapter for Zendesk User Field with shared cursor pagination."""

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def list_all(self) -> Iterable[UserField]:
        for obj in yield_items(
            get_json=self._http.get,
            first_path="/api/v2/user_fields",
            base_url=self._http.base_url,
            items_key="user_fields",
        ):
            yield to_domain(data=obj, cls=UserField)

    def list_options(self, user_field_id: int) -> Iterable[CustomFieldOption]:
        for obj in yield_items(
            get_json=self._http.get,
            first_path=f"/api/v2/user_fields/{user_field_id}/options",
            base_url=self._http.base_url,
            items_key="custom_field_options",
        ):
            yield to_domain(data=obj, cls=CustomFieldOption)

    def get(self, user_field_id: int) -> UserField:
        data = self._http.get(f"/api/v2/user_fields/{int(user_field_id)}")
        return to_domain(data=data["user_field"], cls=UserField)

    def get_option(self, user_field_id: int, user_field_option_id: int) -> CustomFieldOption:
        data = self._http.get(f"/api/v2/user_fields/{int(user_field_id)}/options/{int(user_field_option_id)}")
        return to_domain(data=data["custom_field_option"], cls=CustomFieldOption)
