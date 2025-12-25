from typing import Iterable

from libzapi.domain.models.ticketing.sessions import Session
from libzapi.infrastructure.api_clients.ticketing.session_api_client import SessionApiClient


class SessionsService:
    """High-level service using the API client."""

    def __init__(self, client: SessionApiClient) -> None:
        self._client = client

    def list(self) -> Iterable[Session]:
        return self._client.list()

    def list_user(self, user_id: int) -> Iterable[Session]:
        return self._client.list_user(user_id=user_id)

    def get(self, user_id: int, session_id: int) -> Session:
        return self._client.get(user_id=user_id, session_id=session_id)
