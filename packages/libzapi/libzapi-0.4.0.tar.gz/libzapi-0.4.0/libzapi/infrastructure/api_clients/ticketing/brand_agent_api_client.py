from __future__ import annotations

from typing import Iterator

from libzapi.domain.models.ticketing.brand_agent import BrandAgent
from libzapi.infrastructure.http.client import HttpClient
from libzapi.infrastructure.http.pagination import yield_items
from libzapi.infrastructure.serialization.parse import to_domain


class BrandAgentApiClient:
    """HTTP adapter for Zendesk Brand Agents"""

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def list(self) -> Iterator[BrandAgent]:
        for obj in yield_items(
            get_json=self._http.get,
            first_path="/api/v2/brand_agents",
            base_url=self._http.base_url,
            items_key="brand_agents",
        ):
            yield to_domain(data=obj, cls=BrandAgent)

    def list_by_agent(self, agent_id: int) -> Iterator[BrandAgent]:
        for obj in yield_items(
            get_json=self._http.get,
            first_path=f"/api/v2/users/{int(agent_id)}/brand_agents",
            base_url=self._http.base_url,
            items_key="brand_agents",
        ):
            yield to_domain(data=obj, cls=BrandAgent)

    def list_by_brand(self, brand_id: int) -> Iterator[BrandAgent]:
        for obj in yield_items(
            get_json=self._http.get,
            first_path=f"/api/v2/brands/{int(brand_id)}/agents",
            base_url=self._http.base_url,
            items_key="brand_agents",
        ):
            yield to_domain(data=obj, cls=BrandAgent)

    def get(self, brand_agent_id: int) -> BrandAgent:
        data = self._http.get(f"/api/v2/brand_agents/{int(brand_agent_id)}")
        return to_domain(data=data["brand_agent"], cls=BrandAgent)

    def get_brand_agent_membership(self, agent_id: int, brand_agent_id: int) -> BrandAgent:
        data = self._http.get(f"/api/v2/users/{int(agent_id)}/brand_agents/{int(brand_agent_id)}")
        return to_domain(data=data["brand_agent"], cls=BrandAgent)
