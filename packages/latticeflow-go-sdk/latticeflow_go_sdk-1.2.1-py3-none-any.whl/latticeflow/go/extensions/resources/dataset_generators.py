from __future__ import annotations

from typing import TYPE_CHECKING

from latticeflow.go.models import Error
from latticeflow.go.models import StoredDatasetGenerator
from latticeflow.go.models import Success
from latticeflow.go.types import ApiError


if TYPE_CHECKING:
    from latticeflow.go import AsyncClient
    from latticeflow.go import Client


class DatasetGeneratorsResource:
    def __init__(self, base_client: Client) -> None:
        self._base = base_client

    def get_dataset_generator_by_key(self, key: str) -> StoredDatasetGenerator:
        """Get the Dataset Generator with the given key.

        Args:
            key: The key of the Dataset Generator.

        Raises:
            ApiError: If there is no Dataset Generator with the given key.
        """
        dataset_generators = self._base.dataset_generators.get_dataset_generators(
            key=key
        ).dataset_generators
        if not dataset_generators:
            raise ApiError(
                Error(message=f"Dataset Generator with key '{key}' not found.")
            )

        return dataset_generators[0]

    def delete_dataset_generator_by_key(self, key: str) -> Success:
        """Delete the Dataset Generator by the given key.

        Args:
            key: The key of the Dataset Generator to be deleted.

        Raises:
            ApiError: If there is no Dataset Generator with the given key.
            ApiError: If the deletion of the Dataset Generator fails.
        """
        return self._base.dataset_generators.delete_dataset_generator(
            self._base.dataset_generators.get_dataset_generator_by_key(key=key).id
        )


class AsyncDatasetGeneratorsResource:
    def __init__(self, base_client: AsyncClient) -> None:
        self._base = base_client

    async def get_dataset_generator_by_key(self, key: str) -> StoredDatasetGenerator:
        """Get the Dataset Generator with the given key.

        Args:
            key: The key of the Dataset Generator.

        Raises:
            ApiError: If there is no Dataset Generator with the given key.
        """
        dataset_generators = (
            await self._base.dataset_generators.get_dataset_generators(key=key)
        ).dataset_generators
        if not dataset_generators:
            raise ApiError(
                Error(message=f"Dataset Generator with key '{key}' not found.")
            )

        return dataset_generators[0]

    async def delete_dataset_generator_by_key(self, key: str) -> Success:
        """Delete the Dataset Generator by the given key.

        Args:
            key: The key of the Dataset Generator to be deleted.

        Raises:
            ApiError: If there is no Dataset Generator with the given key.
            ApiError: If the deletion of the Dataset Generator fails.
        """
        return await self._base.dataset_generators.delete_dataset_generator(
            (
                await self._base.dataset_generators.get_dataset_generator_by_key(
                    key=key
                )
            ).id
        )
