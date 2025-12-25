from __future__ import annotations

from typing import Iterable

from libzapi.domain.models.ticketing.sessions import Session
from libzapi.infrastructure.http.client import HttpClient
from libzapi.infrastructure.http.pagination import yield_items
from libzapi.infrastructure.serialization.parse import to_domain


class SessionApiClient:
    """HTTP adapter for Zendesk Workspace"""

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def list(self) -> Iterable[Session]:
        for obj in yield_items(
            get_json=self._http.get,
            first_path="/api/v2/sessions",
            base_url=self._http.base_url,
            items_key="sessions",
        ):
            yield to_domain(data=obj, cls=Session)

    def list_user(self, user_id) -> Iterable[Session]:
        for obj in yield_items(
            get_json=self._http.get,
            first_path=f"/api/v2/users/{user_id}/sessions",
            base_url=self._http.base_url,
            items_key="sessions",
        ):
            yield to_domain(data=obj, cls=Session)

    def get(self, user_id: int, session_id: int) -> Session:
        data = self._http.get(f"/api/v2/users/{int(user_id)}/sessions/{int(session_id)}")
        return to_domain(data=data["session"], cls=Session)
