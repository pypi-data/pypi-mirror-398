from dataclasses import dataclass
from datetime import datetime

from libzapi.domain.shared_objects.logical_key import LogicalKey


@dataclass(frozen=True, slots=True)
class BrandAgent:
    id: int
    url: str
    brand_id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    @property
    def logical_key(self) -> LogicalKey:
        base = f"{self.brand_id}-{self.user_id}"
        return LogicalKey("brand_agent", base)
