from __future__ import annotations

from typing import Iterator

from libzapi.domain.models.ticketing.support_address import RecipientAddress
from libzapi.infrastructure.http.client import HttpClient
from libzapi.infrastructure.http.pagination import yield_items
from libzapi.infrastructure.serialization.parse import to_domain


class SupportAddressApiClient:
    """HTTP adapter for Zendesk Account Settings"""

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def list(self) -> Iterator[RecipientAddress]:
        for obj in yield_items(
            get_json=self._http.get,
            first_path="/api/v2/recipient_addresses",
            base_url=self._http.base_url,
            items_key="recipient_addresses",
        ):
            yield to_domain(data=obj, cls=RecipientAddress)

    def get(self, support_address_id) -> RecipientAddress:
        data = self._http.get(f"/api/v2/recipient_addresses/{support_address_id}")
        return to_domain(data=data["recipient_address"], cls=RecipientAddress)
