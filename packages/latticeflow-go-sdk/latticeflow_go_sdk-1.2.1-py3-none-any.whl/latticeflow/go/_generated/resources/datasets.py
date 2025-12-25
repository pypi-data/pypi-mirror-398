from __future__ import annotations

from typing import Union

from latticeflow.go._generated.api.datasets.create_dataset import (
    asyncio as create_dataset_asyncio,
)
from latticeflow.go._generated.api.datasets.create_dataset import (
    sync as create_dataset_sync,
)
from latticeflow.go._generated.api.datasets.delete_dataset import (
    asyncio as delete_dataset_asyncio,
)
from latticeflow.go._generated.api.datasets.delete_dataset import (
    sync as delete_dataset_sync,
)
from latticeflow.go._generated.api.datasets.get_dataset import (
    asyncio as get_dataset_asyncio,
)
from latticeflow.go._generated.api.datasets.get_dataset import sync as get_dataset_sync
from latticeflow.go._generated.api.datasets.get_dataset_head import (
    asyncio as get_dataset_head_asyncio,
)
from latticeflow.go._generated.api.datasets.get_dataset_head import (
    sync as get_dataset_head_sync,
)
from latticeflow.go._generated.api.datasets.get_datasets import (
    asyncio as get_datasets_asyncio,
)
from latticeflow.go._generated.api.datasets.get_datasets import (
    sync as get_datasets_sync,
)
from latticeflow.go._generated.api.datasets.update_dataset import (
    asyncio as update_dataset_asyncio,
)
from latticeflow.go._generated.api.datasets.update_dataset import (
    sync as update_dataset_sync,
)
from latticeflow.go._generated.api.datasets.update_dataset_data import (
    asyncio as update_dataset_data_asyncio,
)
from latticeflow.go._generated.api.datasets.update_dataset_data import (
    sync as update_dataset_data_sync,
)
from latticeflow.go._generated.models.body import CreateDatasetBody
from latticeflow.go._generated.models.body import UpdateDatasetDataBody
from latticeflow.go._generated.models.model import Dataset
from latticeflow.go._generated.models.model import DatasetData
from latticeflow.go._generated.models.model import Error
from latticeflow.go._generated.models.model import StoredDataset
from latticeflow.go._generated.models.model import StoredDatasets
from latticeflow.go._generated.models.model import Success
from latticeflow.go._generated.types import UNSET
from latticeflow.go._generated.types import Unset
from latticeflow.go.extensions.resources.datasets import (
    AsyncDatasetsResource as AsyncBaseModule,
)
from latticeflow.go.extensions.resources.datasets import DatasetsResource as BaseModule
from latticeflow.go.types import ApiError


class DatasetsResource(BaseModule):
    def get_dataset(self, dataset_id: str) -> StoredDataset:
        """Get a dataset

        Args:
            dataset_id (str):
        """
        with self._base.get_client() as client:
            response = get_dataset_sync(dataset_id=dataset_id, client=client)
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    def get_dataset_head(self, dataset_id: str) -> DatasetData:
        """Get a few sample rows from the dataset csv data file.

        Args:
            dataset_id (str):
        """
        with self._base.get_client() as client:
            response = get_dataset_head_sync(dataset_id=dataset_id, client=client)
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    def update_dataset_data(
        self, dataset_id: str, body: UpdateDatasetDataBody
    ) -> StoredDataset:
        """Update a dataset's data.

        Args:
            dataset_id (str):
            body (UpdateDatasetDataBody):
        """
        with self._base.get_client() as client:
            response = update_dataset_data_sync(
                dataset_id=dataset_id, body=body, client=client
            )
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    def update_dataset(self, dataset_id: str, body: Dataset) -> StoredDataset:
        """Update a dataset

        Args:
            dataset_id (str):
            body (Dataset): All properties required for the creation of a Dataset, except the binary
                file.
        """
        with self._base.get_client() as client:
            response = update_dataset_sync(
                dataset_id=dataset_id, body=body, client=client
            )
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    def get_datasets(
        self,
        *,
        key: Union[Unset, str] = UNSET,
        app_id: Union[Unset, str] = UNSET,
        user_only: Union[Unset, bool] = False,
    ) -> StoredDatasets:
        """Get all registered datasets

        Args:
            key (Union[Unset, str]):
            app_id (Union[Unset, str]):
            user_only (Union[Unset, bool]):  Default: False.
        """
        with self._base.get_client() as client:
            response = get_datasets_sync(
                client=client, key=key, app_id=app_id, user_only=user_only
            )
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    def create_dataset(self, body: CreateDatasetBody) -> StoredDataset:
        """Create a local dataset from a file

        Args:
            body (CreateDatasetBody):
        """
        with self._base.get_client() as client:
            response = create_dataset_sync(body=body, client=client)
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    def delete_dataset(self, dataset_id: str) -> Success:
        """Delete a dataset

        Args:
            dataset_id (str):
        """
        with self._base.get_client() as client:
            response = delete_dataset_sync(dataset_id=dataset_id, client=client)
            if isinstance(response, Error):
                raise ApiError(response)
            return response


class AsyncDatasetsResource(AsyncBaseModule):
    async def get_dataset(self, dataset_id: str) -> StoredDataset:
        """Get a dataset

        Args:
            dataset_id (str):
        """
        with self._base.get_client() as client:
            response = await get_dataset_asyncio(dataset_id=dataset_id, client=client)
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    async def get_dataset_head(self, dataset_id: str) -> DatasetData:
        """Get a few sample rows from the dataset csv data file.

        Args:
            dataset_id (str):
        """
        with self._base.get_client() as client:
            response = await get_dataset_head_asyncio(
                dataset_id=dataset_id, client=client
            )
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    async def update_dataset_data(
        self, dataset_id: str, body: UpdateDatasetDataBody
    ) -> StoredDataset:
        """Update a dataset's data.

        Args:
            dataset_id (str):
            body (UpdateDatasetDataBody):
        """
        with self._base.get_client() as client:
            response = await update_dataset_data_asyncio(
                dataset_id=dataset_id, body=body, client=client
            )
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    async def update_dataset(self, dataset_id: str, body: Dataset) -> StoredDataset:
        """Update a dataset

        Args:
            dataset_id (str):
            body (Dataset): All properties required for the creation of a Dataset, except the binary
                file.
        """
        with self._base.get_client() as client:
            response = await update_dataset_asyncio(
                dataset_id=dataset_id, body=body, client=client
            )
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    async def get_datasets(
        self,
        *,
        key: Union[Unset, str] = UNSET,
        app_id: Union[Unset, str] = UNSET,
        user_only: Union[Unset, bool] = False,
    ) -> StoredDatasets:
        """Get all registered datasets

        Args:
            key (Union[Unset, str]):
            app_id (Union[Unset, str]):
            user_only (Union[Unset, bool]):  Default: False.
        """
        with self._base.get_client() as client:
            response = await get_datasets_asyncio(
                client=client, key=key, app_id=app_id, user_only=user_only
            )
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    async def create_dataset(self, body: CreateDatasetBody) -> StoredDataset:
        """Create a local dataset from a file

        Args:
            body (CreateDatasetBody):
        """
        with self._base.get_client() as client:
            response = await create_dataset_asyncio(body=body, client=client)
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    async def delete_dataset(self, dataset_id: str) -> Success:
        """Delete a dataset

        Args:
            dataset_id (str):
        """
        with self._base.get_client() as client:
            response = await delete_dataset_asyncio(
                dataset_id=dataset_id, client=client
            )
            if isinstance(response, Error):
                raise ApiError(response)
            return response
