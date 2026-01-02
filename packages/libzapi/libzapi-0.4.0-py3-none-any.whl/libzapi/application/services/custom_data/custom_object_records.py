from typing import Iterator, Optional, Iterable

from libzapi.domain.models.custom_data.custom_object_record import CustomObjectRecord
from libzapi.domain.shared_objects.custom_object_limit import CustomObjectLimit
from libzapi.infrastructure.api_clients.custom_data import CustomObjectRecordApiClient
from libzapi.infrastructure.api_clients.custom_data.custom_object_record import SortOrder, SortType


class CustomObjectRecordsService:
    """High-level service using the API client."""

    def __init__(self, client: CustomObjectRecordApiClient) -> None:
        self._client = client

    def list_all(
        self,
        custom_object_key: str,
        external_ids: Optional[Iterable[str]] = None,
        ids: Optional[Iterable[str]] = None,
        page_size: int = 100,
        sort_type: SortType = "id",
        sort_order: SortOrder = "desc",
    ) -> Iterator[CustomObjectRecord]:
        return self._client.list_all(custom_object_key, external_ids, ids, page_size, sort_type, sort_order)

    def get(self, custom_object_key: str, custom_object_record_id: str) -> CustomObjectRecord:
        return self._client.get(custom_object_key=custom_object_key, custom_object_record_id=custom_object_record_id)

    def limit(self) -> CustomObjectLimit:
        return self._client.limit()
