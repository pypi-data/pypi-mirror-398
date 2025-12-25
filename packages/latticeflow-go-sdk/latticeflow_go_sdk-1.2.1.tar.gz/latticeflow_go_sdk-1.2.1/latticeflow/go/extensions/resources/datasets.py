from __future__ import annotations

import asyncio
from io import BytesIO
from pathlib import Path
from typing import TYPE_CHECKING

from latticeflow.go.models import CreateDatasetBody
from latticeflow.go.models import Dataset
from latticeflow.go.models import Error
from latticeflow.go.models import StoredDataset
from latticeflow.go.models import Success
from latticeflow.go.models import UpdateDatasetDataBody
from latticeflow.go.types import ApiError
from latticeflow.go.types import File


if TYPE_CHECKING:
    from latticeflow.go import AsyncClient
    from latticeflow.go import Client


class DatasetsResource:
    def __init__(self, base_client: Client) -> None:
        self._base = base_client

    def _file_from_path(self, path: Path) -> File:
        return File(payload=BytesIO(path.read_bytes()), file_name=path.name)

    def create_dataset_from_path(self, body: Dataset, path: Path) -> StoredDataset:
        """Create a Dataset by uploading a file.

        Args:
            body: The Dataset metadata.
            path: The path to a CSV or JSONL file.
        """
        return self._base.datasets.create_dataset(
            CreateDatasetBody(request=body, file=self._file_from_path(path))
        )

    def update_dataset_data_from_path(
        self, dataset_id: str, path: Path
    ) -> StoredDataset:
        """Update the contents of a Dataset by uploading a file.

        Args:
            dataset_id: The ID of the dataset to be updated.
            path: The path to a CSV or JSONL file.
        """
        return self._base.datasets.update_dataset_data(
            dataset_id=dataset_id,
            body=UpdateDatasetDataBody(file=self._file_from_path(path)),
        )

    def get_dataset_by_key(self, key: str) -> StoredDataset:
        """Get the Dataset with the given key.

        Args:
            key: The key of the Dataset.

        Raises:
            ApiError: If there is no Dataset with the given key.
        """
        datasets = self._base.datasets.get_datasets(key=key).datasets
        if not datasets:
            raise ApiError(Error(message=f"Dataset with key '{key}' not found."))

        return datasets[0]

    def delete_dataset_by_key(self, key: str) -> Success:
        """Delete the Dataset by the given key.

        Args:
            key: The key of the Dataset to be deleted.

        Raises:
            ApiError: If there is no Dataset with the given key.
            ApiError: If the deletion of the Dataset fails.
        """
        return self._base.datasets.delete_dataset(
            self._base.datasets.get_dataset_by_key(key=key).id
        )


class AsyncDatasetsResource:
    def __init__(self, base_client: AsyncClient) -> None:
        self._base = base_client

    async def _file_from_path(self, path: Path) -> File:
        if isinstance(path, str):
            path = Path(path)

        return File(
            payload=BytesIO(await asyncio.to_thread(path.read_bytes)),
            file_name=path.name,
        )

    async def create_dataset_from_path(
        self, body: Dataset, path: Path
    ) -> StoredDataset:
        """Create a Dataset by uploading a file.

        Args:
            body: The Dataset metadata.
            path: The path to a CSV or JSONL file.
        """
        return await self._base.datasets.create_dataset(
            CreateDatasetBody(request=body, file=await self._file_from_path(path))
        )

    async def update_dataset_data_from_path(
        self, dataset_id: str, path: Path
    ) -> StoredDataset:
        """Update the contents of a Dataset by uploading a file.

        Args:
            dataset_id: The ID of the dataset to be updated.
            path: The path to a CSV or JSONL file.
        """
        return await self._base.datasets.update_dataset_data(
            dataset_id=dataset_id,
            body=UpdateDatasetDataBody(file=await self._file_from_path(path)),
        )

    async def get_dataset_by_key(self, key: str) -> StoredDataset:
        """Get the Dataset with the given key.

        Args:
            key: The key of the Dataset.

        Raises:
            ApiError: If there is no Dataset with the given key.
        """
        datasets = (await self._base.datasets.get_datasets(key=key)).datasets
        if not datasets:
            raise ApiError(Error(message=f"Dataset with key '{key}' not found."))

        return datasets[0]

    async def delete_dataset_by_key(self, key: str) -> Success:
        """Delete the Dataset by the given key.

        Args:
            key: The key of the Dataset to be deleted.

        Raises:
            ApiError: If there is no Dataset with the given key.
            ApiError: If the deletion of the Dataset fails.
        """
        return await self._base.datasets.delete_dataset(
            (await self._base.datasets.get_dataset_by_key(key=key)).id
        )
