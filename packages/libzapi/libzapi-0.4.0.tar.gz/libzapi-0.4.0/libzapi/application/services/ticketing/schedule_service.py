from typing import Iterable

from libzapi.domain.models.ticketing.schedule import Schedule, Holiday
from libzapi.infrastructure.api_clients.ticketing.schedule_api_client import ScheduleApiClient


class ScheduleService:
    """High-level service using the API client."""

    def __init__(self, client: ScheduleApiClient) -> None:
        self._client = client

    def list_schedules(self) -> Iterable[Schedule]:
        return self._client.list()

    def get_schedule(self, schedule_id: int) -> Schedule:
        return self._client.get(schedule_id)

    def list_holidays(self, schedule_id: int) -> Iterable[Holiday]:
        return self._client.list_holidays(schedule_id)

    def get_holiday(self, schedule_id: int, holiday_id: int) -> Holiday:
        return self._client.get_holiday(schedule_id, holiday_id)
