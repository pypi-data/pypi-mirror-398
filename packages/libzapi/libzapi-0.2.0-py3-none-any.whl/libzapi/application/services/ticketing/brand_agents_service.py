from typing import Iterable

from libzapi.domain.models.ticketing.brand_agent import BrandAgent
from libzapi.infrastructure.api_clients.ticketing import BrandAgentApiClient


class BrandAgentsService:
    """High-level service using the API client."""

    def __init__(self, client: BrandAgentApiClient) -> None:
        self._client = client

    def list_all(self) -> Iterable[BrandAgent]:
        return self._client.list()

    def list_by_agent(self, agent_id: int) -> Iterable[BrandAgent]:
        return self._client.list_by_agent(agent_id=agent_id)

    def list_by_brand(self, brand_id: int) -> Iterable[BrandAgent]:
        return self._client.list_by_brand(brand_id=brand_id)

    def get_by_brand_agent_id(self, brand_agent_id: int) -> BrandAgent:
        return self._client.get(brand_agent_id=brand_agent_id)

    def get_brand_agent_membership(self, agent_id: int, brand_agent_id: int) -> BrandAgent:
        return self._client.get_brand_agent_membership(agent_id=agent_id, brand_agent_id=brand_agent_id)
