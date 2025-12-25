from __future__ import annotations

from libzapi.domain.models.ticketing.account_settings import Settings
from libzapi.infrastructure.http.client import HttpClient
from libzapi.infrastructure.serialization.parse import to_domain


class AccountSettingsApiClient:
    """HTTP adapter for Zendesk Account Settings"""

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def get(self) -> Settings:
        data = self._http.get("/api/v2/account/settings")
        return to_domain(data=data["settings"], cls=Settings)
