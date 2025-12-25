from typing import Iterable

from libzapi.application.commands.help_center.account_custom_claim_cmds import (
    CreateCustomClaimCmd,
    UpdateCustomClaimCmd,
)
from libzapi.domain.models.help_center.account_custom_claim import CustomClaim
from libzapi.infrastructure.api_clients.help_center import AccountCustomClaimApiClient


class AccountCustomClaimsService:
    """High-level service using the API client."""

    def __init__(self, client: AccountCustomClaimApiClient) -> None:
        self._client = client

    def list_all(self) -> Iterable[CustomClaim]:
        return self._client.list_all()

    def get(self, account_custom_claim_id: str) -> CustomClaim:
        return self._client.get(account_custom_claim_id=account_custom_claim_id)

    def create(
            self,
            claim_identifier: str,
            claim_value: str,
            claim_description: str,
    ) -> CustomClaim:
        cmd = CreateCustomClaimCmd(
            claim_identifier=claim_identifier,
            claim_value=claim_value,
            claim_description=claim_description,
        )
        return self._client.create(cmd=cmd)

    def update(
            self,
            account_custom_claim_id: str,
            claim_identifier: str,
            claim_value: str,
            claim_description: str,
    ) -> CustomClaim:
        cmd = UpdateCustomClaimCmd(
            claim_identifier=claim_identifier,
            claim_value=claim_value,
            claim_description=claim_description,
        )

        return self._client.update(account_custom_claim_id=account_custom_claim_id, cmd=cmd)

    def delete(self, account_custom_claim_id: str) -> None:
        self._client.delete(account_custom_claim_id=account_custom_claim_id)
