from dataclasses import dataclass
from datetime import datetime

from libzapi.domain.shared_objects.logical_key import LogicalKey


@dataclass(frozen=True, slots=True)
class RecipientAddress:
    id: int
    url: str
    brand_id: str
    default: bool
    name: str
    email: str
    forwarding_status: str
    spf_status: str
    cname_status: str
    domain_verification_status: str
    domain_verification_code: str
    created_at: datetime
    updated_at: datetime

    @property
    def logical_key(self) -> LogicalKey:
        base = self.name.lower().replace(" ", "_")
        return LogicalKey("support_address", base)
