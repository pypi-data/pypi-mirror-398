from libzapi.domain.models.ticketing.attachment import Attachment
from libzapi.infrastructure.api_clients.ticketing import AttachmentApiClient


class AttachmentsService:
    """High-level service using the API client."""

    def __init__(self, client: AttachmentApiClient) -> None:
        self._client = client

    def get(self, attachment_id: int) -> Attachment:
        return self._client.get(attachment_id=attachment_id)
