from __future__ import annotations

from typing import Iterator

from libzapi.domain.models.ticketing.email_notification import EmailNotification
from libzapi.infrastructure.http.client import HttpClient
from libzapi.infrastructure.http.pagination import yield_items
from libzapi.infrastructure.serialization.parse import to_domain


class EmailNotificationApiClient:
    """HTTP adapter for Zendesk Email Notification with shared cursor pagination."""

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def list_by_notification_id(self, notification_id: int) -> Iterator[EmailNotification]:
        return self._generic_list(
            filter_key="notification_id",
            filter_value=notification_id,
        )

    def list_by_comment_id(self, comment_id: int) -> Iterator[EmailNotification]:
        return self._generic_list(
            filter_key="comment_id",
            filter_value=comment_id,
        )

    def list_by_ticket_id(self, ticket_id: int) -> Iterator[EmailNotification]:
        return self._generic_list(
            filter_key="ticket_id",
            filter_value=ticket_id,
        )

    def get(self, notification_id: int) -> EmailNotification:
        data = self._http.get(f"/api/v2/email_notifications/{int(notification_id)}")
        return to_domain(data["email_notification"], EmailNotification)

    def _generic_list(self, filter_key: str, filter_value: int) -> Iterator[EmailNotification]:
        for obj in yield_items(
            get_json=self._http.get,
            first_path=f"/api/v2/email_notifications?filter=[{filter_key}]={filter_value}",
            base_url=self._http.base_url,
            items_key="email_notifications",
        ):
            yield to_domain(data=obj, cls=EmailNotification)
