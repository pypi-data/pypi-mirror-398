from __future__ import annotations

from typing import Iterable

from libzapi.domain.models.ticketing.schedule import Schedule, Holiday
from libzapi.infrastructure.http.client import HttpClient
from libzapi.infrastructure.http.pagination import yield_items
from libzapi.infrastructure.serialization.parse import to_domain


class ScheduleApiClient:
    """HTTP adapter for Zendesk Schedule"""

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def list(self) -> Iterable[Schedule]:
        for obj in yield_items(
            get_json=self._http.get,
            first_path="/api/v2/business_hours/schedules",
            base_url=self._http.base_url,
            items_key="schedules",
        ):
            yield to_domain(data=obj, cls=Schedule)

    def list_holidays(self, schedule_id) -> Iterable[Holiday]:
        for obj in yield_items(
            get_json=self._http.get,
            first_path=f"/api/v2/business_hours/schedules/{schedule_id}/holidays",
            base_url=self._http.base_url,
            items_key="holidays",
        ):
            yield to_domain(data=obj, cls=Holiday)

    def get(self, schedule_id: int) -> Schedule:
        data = self._http.get(f"/api/v2/business_hours/schedules/{schedule_id}")
        return to_domain(data=data["schedule"], cls=Schedule)

    def get_holiday(self, schedule_id: int, holiday_id) -> Holiday:
        data = self._http.get(f"/api/v2/business_hours/schedules/{schedule_id}/holidays/{holiday_id}")
        return to_domain(data=data["holiday"], cls=Holiday)
