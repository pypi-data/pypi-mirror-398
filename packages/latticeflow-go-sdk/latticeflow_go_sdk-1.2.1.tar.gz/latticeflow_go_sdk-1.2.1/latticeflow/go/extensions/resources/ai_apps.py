from __future__ import annotations

from typing import TYPE_CHECKING

from latticeflow.go.models import Error
from latticeflow.go.models import StoredAIApp
from latticeflow.go.models import Success
from latticeflow.go.types import ApiError


if TYPE_CHECKING:
    from latticeflow.go import AsyncClient
    from latticeflow.go import Client


class AiAppsResource:
    def __init__(self, base_client: Client) -> None:
        self._base = base_client

    def get_ai_app_by_key(self, key: str) -> StoredAIApp:
        """Get the AI App with the given key.

        Args:
            key: The key of the AI App.

        Raises:
            ApiError: If there is no AI App with the given key.
        """
        ai_apps = self._base.ai_apps.get_ai_apps(key=key).ai_apps
        if not ai_apps:
            raise ApiError(Error(message=f"AI App with key '{key}' not found."))

        return ai_apps[0]

    def delete_ai_app_by_key(self, key: str) -> Success:
        """Delete the AI App by the given key.

        Args:
            key: The key of the AI App to be deleted.

        Raises:
            ApiError: If there is no AI App with the given key.
            ApiError: If the deletion of the AI App fails.
        """
        return self._base.ai_apps.delete_ai_app(
            self._base.ai_apps.get_ai_app_by_key(key=key).id
        )


class AsyncAiAppsResource:
    def __init__(self, base_client: AsyncClient) -> None:
        self._base = base_client

    async def get_ai_app_by_key(self, key: str) -> StoredAIApp:
        """Get the AI App with the given key.

        Args:
            key: The key of the AI App.

        Raises:
            ApiError: If there is no AI App with the given key.
        """
        ai_apps = (await self._base.ai_apps.get_ai_apps(key=key)).ai_apps
        if not ai_apps:
            raise ApiError(Error(message=f"AI App with key '{key}' not found."))

        return ai_apps[0]

    async def delete_ai_app_by_key(self, key: str) -> Success:
        """Delete the AI App by the given key.

        Args:
            key: The key of the AI App to be deleted.

        Raises:
            ApiError: If there is no AI App with the given key.
            ApiError: If the deletion of the AI App fails.
        """
        return await self._base.ai_apps.delete_ai_app(
            (await self._base.ai_apps.get_ai_app_by_key(key=key)).id
        )
