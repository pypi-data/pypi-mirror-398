from __future__ import annotations

from libzapi.domain.models.ticketing.attachment import Attachment
from libzapi.infrastructure.http.client import HttpClient
from libzapi.infrastructure.serialization.parse import to_domain


class AttachmentApiClient:
    """HTTP adapter for Zendesk Attachments API."""

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def get(self, attachment_id: int) -> Attachment:
        data = self._http.get(f"/api/v2/attachments/{int(attachment_id)}")
        return to_domain(data=data["attachment"], cls=Attachment)
