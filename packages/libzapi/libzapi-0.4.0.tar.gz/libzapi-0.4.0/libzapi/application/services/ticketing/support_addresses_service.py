from typing import Iterable

from libzapi.domain.models.ticketing.support_address import RecipientAddress
from libzapi.infrastructure.api_clients.ticketing.support_address_api_client import SupportAddressApiClient


class SupportAddressesService:
    """High-level service using the API client."""

    def __init__(self, client: SupportAddressApiClient) -> None:
        self._client = client

    def list(self) -> Iterable[RecipientAddress]:
        return self._client.list()

    def get(self, support_address_id: int) -> RecipientAddress:
        return self._client.get(support_address_id)
