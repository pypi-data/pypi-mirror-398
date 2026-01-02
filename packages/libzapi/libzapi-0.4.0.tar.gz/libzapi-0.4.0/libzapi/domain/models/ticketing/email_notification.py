from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List

from libzapi.domain.shared_objects.logical_key import LogicalKey


@dataclass(frozen=True, slots=True)
class DeliveryStatus:
    id: int
    name: str
    code: str
    message: str


@dataclass(frozen=True, slots=True)
class Recipient:
    user_id: int
    email_address: str
    delivery_status: DeliveryStatus


@dataclass(frozen=True, slots=True)
class EmailNotification:
    id: int
    url: str
    notification_id: int
    ticket_id: int
    recipients: List[Recipient]
    comment_id: Optional[int] = None
    message_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @property
    def logical_key(self) -> LogicalKey:
        base = f"id_{self.notification_id}"
        return LogicalKey("email_notification", base)
