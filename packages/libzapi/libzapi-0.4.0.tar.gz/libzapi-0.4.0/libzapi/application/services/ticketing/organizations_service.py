from typing import Iterable

from libzapi.domain.models.ticketing.organization import Organization
from libzapi.domain.shared_objects.count_snapshot import CountSnapshot
from libzapi.infrastructure.api_clients.ticketing.organization_api_client import OrganizationApiClient


class OrganizationsService:
    """High-level service using the API client."""

    def __init__(self, client: OrganizationApiClient) -> None:
        self._client = client

    def list_all(self) -> Iterable[Organization]:
        return self._client.list()

    def list_by_user(self, user_id: int) -> Iterable[Organization]:
        return self._client.list_organizations(user_id)

    def count(self) -> CountSnapshot:
        return self._client.count()

    def get_by_id(self, organization_id: int) -> Organization:
        return self._client.get(organization_id)

    def search(self, external_id: str | None = None, name: str | None = None) -> Iterable[Organization]:
        return self._client.search(external_id=external_id, name=name)
