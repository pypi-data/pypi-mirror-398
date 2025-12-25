from __future__ import annotations

from typing import TYPE_CHECKING

from latticeflow.go.models import Error
from latticeflow.go.models import StoredModelAdapter
from latticeflow.go.models import Success
from latticeflow.go.types import ApiError


if TYPE_CHECKING:
    from latticeflow.go import AsyncClient
    from latticeflow.go import Client


class ModelAdaptersResource:
    def __init__(self, base_client: Client) -> None:
        self._base = base_client

    def get_model_adapter_by_key(self, key: str) -> StoredModelAdapter:
        """Get the Model Adapter with the given key.

        Args:
            key: The key of the Model Adapter.

        Raises:
            ApiError: If there is no Model Adapter with the given key.
        """
        model_adapters = self._base.model_adapters.get_model_adapters(
            key=key
        ).model_adapters
        if not model_adapters:
            raise ApiError(Error(message=f"Model Adapter with key '{key}' not found."))

        return model_adapters[0]

    def delete_model_adapter_by_key(self, key: str) -> Success:
        """Delete the Model Adapter by the given key.

        Args:
            key: The key of the Model Adapter to be deleted.

        Raises:
            ApiError: If there is no Model Adapter with the given key.
            ApiError: If the deletion of the Model Adapter fails.
        """
        return self._base.model_adapters.delete_model_adapter(
            self._base.model_adapters.get_model_adapter_by_key(key=key).id
        )


class AsyncModelAdaptersResource:
    def __init__(self, base_client: AsyncClient) -> None:
        self._base = base_client

    async def get_model_adapter_by_key(self, key: str) -> StoredModelAdapter:
        """Get the Model Adapter with the given key.

        Args:
            key: The key of the Model Adapter.

        Raises:
            ApiError: If there is no Model Adapter with the given key.
        """
        model_adapters = (
            await self._base.model_adapters.get_model_adapters(key=key)
        ).model_adapters
        if not model_adapters:
            raise ApiError(Error(message=f"Model Adapter with key '{key}' not found."))

        return model_adapters[0]

    async def delete_model_adapter_by_key(self, key: str) -> Success:
        """Delete the Model Adapter by the given key.

        Args:
            key: The key of the Model Adapter to be deleted.

        Raises:
            ApiError: If there is no Model Adapter with the given key.
            ApiError: If the deletion of the Model Adapter fails.
        """
        return await self._base.model_adapters.delete_model_adapter(
            (await self._base.model_adapters.get_model_adapter_by_key(key=key)).id
        )
