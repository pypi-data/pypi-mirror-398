from __future__ import annotations

from typing import Iterator

from libzapi.domain.models.ticketing.brand import Brand
from libzapi.infrastructure.http.client import HttpClient
from libzapi.infrastructure.http.pagination import yield_items
from libzapi.infrastructure.serialization.parse import to_domain


class BrandApiClient:
    """HTTP adapter for Zendesk Brands"""

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def list(self) -> Iterator[Brand]:
        for obj in yield_items(
            get_json=self._http.get,
            first_path="/api/v2/brands",
            base_url=self._http.base_url,
            items_key="brands",
        ):
            yield to_domain(data=obj, cls=Brand)

    def get(self, brand_id: int) -> Brand:
        data = self._http.get(f"/api/v2/brands/{int(brand_id)}")
        return to_domain(data=data["brand"], cls=Brand)
