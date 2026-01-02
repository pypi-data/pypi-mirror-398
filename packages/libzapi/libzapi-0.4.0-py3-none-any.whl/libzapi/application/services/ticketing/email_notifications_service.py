from typing import Iterable

from libzapi.domain.models.ticketing.email_notification import EmailNotification
from libzapi.infrastructure.api_clients.ticketing import EmailNotificationApiClient


class EmailNotificationService:
    """High-level service using the API client."""

    def __init__(self, client: EmailNotificationApiClient) -> None:
        self._client = client

    def list_by_notification_id(self, notification_id: int) -> Iterable[EmailNotification]:
        return self._client.list_by_notification_id(notification_id)

    def list_by_comment_id(self, comment_id: int) -> Iterable[EmailNotification]:
        return self._client.list_by_comment_id(comment_id)

    def list_by_ticket_id(self, ticket_id: int) -> Iterable[EmailNotification]:
        return self._client.list_by_ticket_id(ticket_id)

    def get(self, notification_id: int) -> EmailNotification:
        return self._client.get(notification_id=notification_id)
