from dataclasses import dataclass
from datetime import datetime

from libzapi.domain.shared_objects.logical_key import LogicalKey


@dataclass(frozen=True, slots=True)
class RedirectRule:
    id: str
    brand_id: int  # For consistency with other models that have brand_id field as int
    redirect_from: str
    redirect_status: int  # e.g., 301, 302
    redirect_to: str
    created_at: datetime | None
    updated_at: datetime | None

    @property
    def logical_key(self) -> LogicalKey:
        base = f"id_{self.id}".lower().replace(" ", "_")
        return LogicalKey("redirect_rule", base)
