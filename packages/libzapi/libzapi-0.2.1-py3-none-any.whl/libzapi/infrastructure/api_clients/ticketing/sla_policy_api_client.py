from __future__ import annotations

from typing import Iterator

from libzapi.domain.models.ticketing.sla_policies import SlaPolicy
from libzapi.infrastructure.http.client import HttpClient
from libzapi.infrastructure.http.pagination import yield_items
from libzapi.infrastructure.serialization.parse import to_domain


class SlaPolicyApiClient:
    """HTTP adapter for Zendesk Sla Policies with shared cursor pagination."""

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def list(self) -> Iterator[SlaPolicy]:
        for obj in yield_items(
            get_json=self._http.get,
            first_path="/api/v2/slas/policies",
            base_url=self._http.base_url,
            items_key="sla_policies",
        ):
            yield to_domain(data=obj, cls=SlaPolicy)

    def get(self, sla_policy_id: int) -> SlaPolicy:
        data = self._http.get(f"/api/v2/slas/policies/{int(sla_policy_id)}")
        return to_domain(data=data["sla_policy"], cls=SlaPolicy)
