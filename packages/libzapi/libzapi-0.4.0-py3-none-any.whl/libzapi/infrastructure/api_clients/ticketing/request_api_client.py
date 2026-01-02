from __future__ import annotations

from typing import Iterable

from libzapi.domain.models.ticketing.request import Request
from libzapi.infrastructure.http.client import HttpClient
from libzapi.infrastructure.http.pagination import yield_items
from libzapi.infrastructure.serialization.parse import to_domain


class RequestApiClient:
    """HTTP adapter for Zendesk Groups with shared cursor pagination."""

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def list_user(self, user_id: int) -> Iterable[Request]:
        for obj in yield_items(
            get_json=self._http.get,
            first_path=f"/api/v2/users/{int(user_id)}/requests",
            base_url=self._http.base_url,
            items_key="requests",
        ):
            yield to_domain(data=obj, cls=Request)

    def get(self, request_id: int) -> Request:
        data = self._http.get(f"/api/v2/requests/{int(request_id)}")
        return to_domain(data=data["request"], cls=Request)
