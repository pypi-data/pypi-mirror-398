from __future__ import annotations

from typing import Iterator

from libzapi.application.commands.help_center.section_cmds import (
    UpdateSectionCmd,
    CreateSectionCmd,
)
from libzapi.domain.models.help_center.section import Section
from libzapi.infrastructure.http.client import HttpClient
from libzapi.infrastructure.http.pagination import yield_items
from libzapi.infrastructure.mappers.help_center.section_mapper import (
    to_payload_create,
    to_payload_update,
)
from libzapi.infrastructure.serialization.parse import to_domain


class SectionApiClient:
    """HTTP adapter for Zendesk Sections in Help Center"""

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def list_all(self) -> Iterator[Section]:
        for obj in yield_items(
            get_json=self._http.get,
            first_path="/api/v2/help_center/sections",
            base_url=self._http.base_url,
            items_key="sections",
        ):
            yield to_domain(data=obj, cls=Section)

    def get(self, section_id: int) -> Section:
        data = self._http.get(f"/api/v2/help_center/sections/{int(section_id)}")
        return to_domain(data=data["section"], cls=Section)

    def create(self, category_id: int, cmd: CreateSectionCmd) -> Section:
        payload = to_payload_create(cmd)
        data = self._http.post(f"/api/v2/help_center/categories/{int(category_id)}/sections", json=payload)
        return to_domain(data=data["section"], cls=Section)

    def update(self, section_id: int, locale: str, cmd: UpdateSectionCmd) -> Section:
        payload = to_payload_update(cmd)
        data = self._http.put(f"/api/v2/help_center/{locale}/sections/{int(section_id)}", json=payload)
        return to_domain(data=data["section"], cls=Section)

    def delete(self, section_id: int) -> None:
        self._http.delete(f"/api/v2/help_center/sections/{int(section_id)}")
