from __future__ import annotations

from typing import Iterator

from libzapi.application.commands.help_center.account_custom_claim_cmds import CreateCustomClaimCmd, \
    UpdateCustomClaimCmd
from libzapi.domain.models.help_center.account_custom_claim import CustomClaim
from libzapi.infrastructure.http.client import HttpClient
from libzapi.infrastructure.http.pagination import yield_items
from libzapi.infrastructure.mappers.help_center.account_custom_claim_mapper import (
    to_payload_create,
    to_payload_update,
)
from libzapi.infrastructure.serialization.parse import to_domain


class AccountCustomClaimApiClient:
    """HTTP adapter for Zendesk Account Custom Claims in Help Center"""

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def list_all(self) -> Iterator[CustomClaim]:
        for obj in yield_items(
                get_json=self._http.get,
                first_path="/api/v2/help_center/integration/account_custom_claims",
                base_url=self._http.base_url,
                items_key="custom_claims",
        ):
            yield to_domain(data=obj, cls=CustomClaim)

    def get(self, account_custom_claim_id: str) -> CustomClaim:
        data = self._http.get(f"/api/v2/help_center/integration/account_custom_claims/{account_custom_claim_id}")
        return to_domain(data=data["custom_claim"], cls=CustomClaim)

    def create(self, cmd: CreateCustomClaimCmd) -> CustomClaim:
        payload = to_payload_create(cmd)
        data = self._http.post("/api/v2/help_center/integration/account_custom_claims", json=payload)
        return to_domain(data=data["custom_claim"], cls=CustomClaim)

    def update(self, account_custom_claim_id: str, cmd: UpdateCustomClaimCmd) -> CustomClaim:
        payload = to_payload_update(cmd)
        data = self._http.put(f"/api/v2/help_center/integration/account_custom_claims/{account_custom_claim_id}",
                              json=payload)
        return to_domain(data=data["custom_claim"], cls=CustomClaim)

    def delete(self, account_custom_claim_id: str) -> None:
        self._http.delete(f"/api/v2/help_center/integration/account_custom_claims/{account_custom_claim_id}")
