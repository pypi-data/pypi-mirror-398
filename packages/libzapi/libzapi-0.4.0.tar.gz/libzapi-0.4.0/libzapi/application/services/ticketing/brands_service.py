from typing import Iterable

from libzapi.domain.models.ticketing.brand import Brand
from libzapi.infrastructure.api_clients.ticketing import BrandApiClient


class BrandsService:
    """High-level service using the API client."""

    def __init__(self, client: BrandApiClient) -> None:
        self._client = client

    def list(self) -> Iterable[Brand]:
        return self._client.list()

    def get(self, brand_id: int) -> Brand:
        return self._client.get(brand_id=brand_id)
