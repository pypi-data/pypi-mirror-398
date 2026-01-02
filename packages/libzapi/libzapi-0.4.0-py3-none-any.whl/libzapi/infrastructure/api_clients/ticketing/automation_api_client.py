from __future__ import annotations

from typing import Iterator

from libzapi.domain.models.ticketing.automation import Automation
from libzapi.infrastructure.http.client import HttpClient
from libzapi.infrastructure.http.pagination import yield_items
from libzapi.infrastructure.serialization.parse import to_domain


class AutomationApiClient:
    """HTTP adapter for Zendesk Automations"""

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def list_all(self) -> Iterator[Automation]:
        for obj in yield_items(
            get_json=self._http.get,
            first_path="/api/v2/automations",
            base_url=self._http.base_url,
            items_key="automations",
        ):
            yield to_domain(data=obj, cls=Automation)

    def list_active(self) -> Iterator[Automation]:
        for obj in yield_items(
            get_json=self._http.get,
            first_path="/api/v2/automations/active",
            base_url=self._http.base_url,
            items_key="automations",
        ):
            yield to_domain(data=obj, cls=Automation)

    def get(self, automation_id: int) -> Automation:
        data = self._http.get(f"/api/v2/automations/{int(automation_id)}")
        return to_domain(data=data["automation"], cls=Automation)
