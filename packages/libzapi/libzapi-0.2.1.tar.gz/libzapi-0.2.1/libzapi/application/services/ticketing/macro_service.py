from typing import Iterable

from libzapi.domain.models.ticketing.macro import Macro
from libzapi.infrastructure.api_clients.ticketing import MacroApiClient


class MacroService:
    """High-level service using the API client."""

    def __init__(self, client: MacroApiClient) -> None:
        self._client = client

    def list(self) -> Iterable[Macro]:
        return self._client.list()

    def list_active(self) -> Iterable[Macro]:
        return self._client.list_active()

    def get(self, macro_id: int) -> Macro:
        return self._client.get(macro_id=macro_id)
