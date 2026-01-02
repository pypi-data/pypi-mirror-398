from __future__ import annotations

from typing import Iterator

from libzapi.application.commands.help_center.category_cmds import (
    CreateCategoryCmd,
    UpdateCategoryCmd,
)
from libzapi.domain.models.help_center.category import Category
from libzapi.infrastructure.http.client import HttpClient
from libzapi.infrastructure.http.pagination import yield_items
from libzapi.infrastructure.mappers.help_center.category_mapper import (
    to_payload_create,
    to_payload_update,
)
from libzapi.infrastructure.serialization.parse import to_domain


class CategoryApiClient:
    """HTTP adapter for Zendesk Categories in Help Center"""

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def list_all(self) -> Iterator[Category]:
        for obj in yield_items(
            get_json=self._http.get,
            first_path="/api/v2/help_center/categories",
            base_url=self._http.base_url,
            items_key="categories",
        ):
            yield to_domain(data=obj, cls=Category)

    def get(self, category_id: int) -> Category:
        data = self._http.get(f"/api/v2/help_center/categories/{int(category_id)}")
        return to_domain(data=data["category"], cls=Category)

    def create(self, cmd: CreateCategoryCmd) -> Category:
        payload = to_payload_create(cmd)
        data = self._http.post("/api/v2/help_center/categories", json=payload)
        return to_domain(data=data["category"], cls=Category)

    def update(self, category_id: int, cmd: UpdateCategoryCmd) -> Category:
        payload = to_payload_update(cmd)
        data = self._http.put(f"/api/v2/help_center/categories/{int(category_id)}", json=payload)
        return to_domain(data=data["category"], cls=Category)

    def delete(self, category_id: int) -> None:
        self._http.delete(f"/api/v2/help_center/categories/{int(category_id)}")
