from typing import Iterable

from libzapi.application.commands.help_center.category_cmds import (
    CreateCategoryCmd,
    UpdateCategoryCmd,
)
from libzapi.domain.models.help_center.category import Category
from libzapi.infrastructure.api_clients.help_center import CategoryApiClient


class CategoriesService:
    """High-level service using the API client."""

    def __init__(self, client: CategoryApiClient) -> None:
        self._client = client

    def list_all(self) -> Iterable[Category]:
        return self._client.list_all()

    def get(self, category_id: int) -> Category:
        return self._client.get(category_id=category_id)

    def create(
        self,
        name,
        locale,
        description,
        position,
    ) -> Category:
        cmd = CreateCategoryCmd(
            name=name,
            description=description,
            locale=locale,
            position=position,
        )
        return self._client.create(cmd=cmd)

    def update(self, category_id: int, name, description, position) -> Category:
        cmd = UpdateCategoryCmd(
            name=name,
            description=description,
            position=position,
        )

        return self._client.update(category_id=category_id, cmd=cmd)

    def delete(self, category_id: int) -> None:
        self._client.delete(category_id=category_id)
