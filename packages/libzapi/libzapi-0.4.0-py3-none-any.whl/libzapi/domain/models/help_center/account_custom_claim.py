from dataclasses import dataclass
from datetime import datetime

from libzapi.domain.shared_objects.logical_key import LogicalKey


@dataclass(frozen=True, slots=True)
class CustomClaim:
    id: str
    account_id: int
    brand_id: int
    claim_identifier: str
    claim_value: str
    claim_description: str
    created_at: datetime | None
    updated_at: datetime | None

    @property
    def logical_key(self) -> LogicalKey:
        base = self.claim_identifier.lower().replace(" ", "_")
        return LogicalKey("custom_claim", base)
