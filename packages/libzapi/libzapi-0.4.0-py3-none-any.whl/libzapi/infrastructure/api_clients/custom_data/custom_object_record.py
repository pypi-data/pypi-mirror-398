from typing import Iterator, TypeAlias, Literal, Iterable

from libzapi.domain.models.custom_data.custom_object_record import CustomObjectRecord
from libzapi.domain.shared_objects.custom_object_limit import CustomObjectLimit
from libzapi.infrastructure.http.client import HttpClient
from libzapi.infrastructure.http.pagination import yield_items
from libzapi.infrastructure.serialization.parse import to_domain

_ALLOWED_SORT_TYPES = {"id", "updated_at"}
_ALLOWED_SORT_ORDERS = {"asc", "desc"}

SortType: TypeAlias = Literal["id", "updated_at"]
SortOrder: TypeAlias = Literal["asc", "desc"]


class CustomObjectRecordApiClient:
    """HTTP adapter for Zendesk Custom Objects Records API."""

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def list_all(
        self,
        custom_object_key: str,
        external_ids: Iterable,
        ids: Iterable,
        page_size: int,
        sort_type: SortType,
        sort_order: SortOrder,
    ) -> Iterator[CustomObjectRecord]:
        query = build_query(
            external_ids=external_ids, ids=ids, page_size=page_size, sort_type=sort_type, sort_order=sort_order
        )
        for obj in yield_items(
            get_json=self._http.get,
            first_path=f"/api/v2/custom_objects/{custom_object_key}/records?{query}",
            base_url=self._http.base_url,
            items_key="custom_object_records",
        ):
            yield to_domain(data=obj, cls=CustomObjectRecord)

    def get(self, custom_object_key: str, custom_object_record_id: str) -> CustomObjectRecord:
        data = self._http.get(f"/api/v2/custom_objects/{custom_object_key}/records/{custom_object_record_id}")
        return to_domain(data=data["custom_object_record"], cls=CustomObjectRecord)

    def create(self, payload: dict) -> CustomObjectRecord:
        raise NotImplementedError

    def update(self, custom_object_id: str, data: dict) -> CustomObjectRecord:
        raise NotImplementedError

    def delete(self, custom_object_id: str) -> CustomObjectRecord:
        raise NotImplementedError

    def limit(self) -> CustomObjectLimit:
        data = self._http.get("/api/v2/custom_objects/limits/record_limit")
        return to_domain(data=data, cls=CustomObjectLimit)


def build_query(
    external_ids: Iterable, ids: Iterable, page_size: int, sort_type: SortType, sort_order: SortOrder
) -> str:
    query_parts = []
    if sort_type not in _ALLOWED_SORT_TYPES:
        raise ValueError(f"Invalid sort_type: {sort_type}")

    if sort_order not in _ALLOWED_SORT_ORDERS:
        raise ValueError(f"Invalid sort_order: {sort_order}")

    if external_ids:
        external_ids_str = ",".join(external_ids)
        query_parts.append(f"filter[external_ids]={external_ids_str}")
    if ids:
        ids_str = ",".join(ids)
        query_parts.append(f"filter[ids]={ids_str}")
    if page_size:
        query_parts.append(f"page[size]={page_size}")
    if sort_type:
        sort_prefix = "" if sort_order == "asc" else "-"
        query_parts.append(f"sort={sort_prefix}{sort_type}")
    return "&".join(query_parts)
