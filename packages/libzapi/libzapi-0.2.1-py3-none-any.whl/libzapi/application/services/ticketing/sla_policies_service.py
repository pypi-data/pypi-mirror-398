from typing import Iterable

from libzapi.domain.models.ticketing.sla_policies import SlaPolicy
from libzapi.infrastructure.api_clients.ticketing.sla_policy_api_client import SlaPolicyApiClient


class SlaPoliciesService:
    """High-level service using the API client."""

    def __init__(self, client: SlaPolicyApiClient) -> None:
        self._client = client

    def list(self) -> Iterable[SlaPolicy]:
        return self._client.list()

    def get(self, sla_policy_id: int) -> SlaPolicy:
        return self._client.get(sla_policy_id=sla_policy_id)
