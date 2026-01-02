from libzapi.domain.models.ticketing.account_settings import Settings
from libzapi.infrastructure.api_clients.ticketing.account_settings_api_client import AccountSettingsApiClient


class AccountSettingsService:
    """High-level service using the API client."""

    def __init__(self, client: AccountSettingsApiClient) -> None:
        self._client = client

    def get(self) -> Settings:
        return self._client.get()
