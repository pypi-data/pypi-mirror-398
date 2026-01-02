from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from libzapi.domain.shared_objects.logical_key import LogicalKey
from libzapi.domain.shared_objects.thumbnail import Thumbnail

OrganizationIdType = int | list[int] | None


@dataclass(frozen=True, slots=True)
class User:
    id: int
    url: str
    name: str
    email: str
    created_at: datetime
    updated_at: datetime
    time_zone: str
    iana_time_zone: str
    phone: str
    shared_phone_number: bool
    photo: Optional[Thumbnail]
    locale_id: int
    locale: str
    organization_id: Optional[OrganizationIdType]
    role: str
    verified: bool
    external_id: str
    tags: List[str]
    alias: str
    active: bool
    shared: bool
    shared_agent: bool
    last_login_at: datetime
    two_factor_auth_enabled: bool
    signature: str
    details: str
    notes: str
    role_type: Optional[int]
    custom_role_id: Optional[int]
    is_billing_admin: bool
    moderator: bool
    ticket_restriction: str
    only_private_comments: bool
    restricted_agent: bool
    suspended: bool
    default_group_id: Optional[int]
    report_csv: bool
    user_fields: dict

    @property
    def logical_key(self) -> LogicalKey:
        base = f"id_{self.id}"
        return LogicalKey("user", base)
