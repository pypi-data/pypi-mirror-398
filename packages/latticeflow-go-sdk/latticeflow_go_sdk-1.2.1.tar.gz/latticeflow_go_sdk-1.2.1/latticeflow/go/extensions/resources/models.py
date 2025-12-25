from __future__ import annotations

from typing import TYPE_CHECKING

from latticeflow.go.models import Error
from latticeflow.go.models import StoredModel
from latticeflow.go.models import Success
from latticeflow.go.types import ApiError


if TYPE_CHECKING:
    from latticeflow.go import AsyncClient
    from latticeflow.go import Client


class ModelsResource:
    def __init__(self, base_client: Client) -> None:
        self._base = base_client

    def get_model_by_key(self, key: str) -> StoredModel:
        """Get the Model with the given key.

        Args:
            key: The key of the Model.

        Raises:
            ApiError: If there is no Model with the given key.
        """
        models = self._base.models.get_models(key=key).models
        if not models:
            raise ApiError(Error(message=f"Model with key '{key}' not found."))

        return models[0]

    def delete_model_by_key(self, key: str) -> Success:
        """Delete the Model by the given key.

        Args:
            key: The key of the Model to be deleted.

        Raises:
            ApiError: If there is no Model with the given key.
            ApiError: If the deletion of the Model fails.
        """
        return self._base.models.delete_model(
            self._base.models.get_model_by_key(key=key).id
        )


class AsyncModelsResource:
    def __init__(self, base_client: AsyncClient) -> None:
        self._base = base_client

    async def get_model_by_key(self, key: str) -> StoredModel:
        """Get the Model with the given key.

        Args:
            key: The key of the Model.

        Raises:
            ApiError: If there is no Model with the given key.
        """
        models = (await self._base.models.get_models(key=key)).models
        if not models:
            raise ApiError(Error(message=f"Model with key '{key}' not found."))

        return models[0]

    async def delete_model_by_key(self, key: str) -> Success:
        """Delete the Model by the given key.

        Args:
            key: The key of the Model to be deleted.

        Raises:
            ApiError: If there is no Model with the given key.
            ApiError: If the deletion of the Model fails.
        """
        return await self._base.models.delete_model(
            (await self._base.models.get_model_by_key(key=key)).id
        )
