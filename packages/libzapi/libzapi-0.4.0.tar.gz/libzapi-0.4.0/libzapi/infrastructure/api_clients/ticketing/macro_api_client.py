from __future__ import annotations

from typing import Iterator

from libzapi.domain.models.ticketing.macro import Macro
from libzapi.infrastructure.http.client import HttpClient
from libzapi.infrastructure.http.pagination import yield_items
from libzapi.infrastructure.serialization.parse import to_domain


class MacroApiClient:
    """HTTP adapter for Zendesk Macros with shared cursor pagination."""

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def list(self) -> Iterator[Macro]:
        for obj in yield_items(
            get_json=self._http.get,
            first_path="/api/v2/macros",
            base_url=self._http.base_url,
            items_key="macros",
        ):
            yield to_domain(data=obj, cls=Macro)

    def list_active(self) -> Iterator[Macro]:
        for obj in yield_items(
            get_json=self._http.get,
            first_path="/api/v2/macros/active",
            base_url=self._http.base_url,
            items_key="macros",
        ):
            yield to_domain(data=obj, cls=Macro)

    def get(self, macro_id: int) -> Macro:
        data = self._http.get(f"/api/v2/macros/{int(macro_id)}")
        return to_domain(data["macro"], Macro)
