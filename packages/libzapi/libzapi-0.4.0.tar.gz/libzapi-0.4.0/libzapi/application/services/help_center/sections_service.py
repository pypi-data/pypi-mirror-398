from typing import Iterable

from libzapi.application.commands.help_center.section_cmds import (
    CreateSectionCmd,
    UpdateSectionCmd,
)
from libzapi.domain.models.help_center.section import Section
from libzapi.infrastructure.api_clients.help_center import SectionApiClient


class SectionsService:
    """High-level service using the API client."""

    def __init__(self, client: SectionApiClient) -> None:
        self._client = client

    def list_all(self) -> Iterable[Section]:
        return self._client.list_all()

    def get(self, section_id: int) -> Section:
        return self._client.get(section_id=section_id)

    def create(
        self,
        category_id: int,
        name,
        locale,
        description,
        position,
        parent_section_id: int = None,
    ) -> Section:
        cmd = CreateSectionCmd(
            name=name,
            description=description,
            locale=locale,
            position=position,
            parent_section_id=parent_section_id,
        )
        return self._client.create(category_id=category_id, cmd=cmd)

    def update(
        self,
        section_id: int,
        locale,
        name=None,
        description=None,
        position=None,
        category_id=None,
        parent_section_id=None,
        promote_to_top_level=False,
    ) -> Section:
        cmd = UpdateSectionCmd(
            name=name,
            description=description,
            position=position,
            category_id=category_id,
            parent_section_id=parent_section_id,
            promote_to_top_level=promote_to_top_level,
        )

        return self._client.update(section_id=section_id, locale=locale, cmd=cmd)

    def delete(self, section_id: int) -> None:
        self._client.delete(section_id=section_id)
