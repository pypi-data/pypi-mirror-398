from typing import Iterable

from libzapi.infrastructure.api_clients.ticketing.request_api_client import RequestApiClient
from libzapi.domain.models.ticketing.request import Request


class RequestsService:
    """High-level service using the API client."""

    def __init__(self, client: RequestApiClient) -> None:
        self._client = client

    def list_by_user(self, user_id) -> Iterable[Request]:
        return self._client.list_user(user_id)

    def get_by_id(self, request_id: int) -> Request:
        return self._client.get(request_id)
