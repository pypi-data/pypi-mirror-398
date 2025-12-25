from __future__ import annotations

from typing import Union

from latticeflow.go._generated.api.dataset_generators.create_dataset_generator import (
    asyncio as create_dataset_generator_asyncio,
)
from latticeflow.go._generated.api.dataset_generators.create_dataset_generator import (
    sync as create_dataset_generator_sync,
)
from latticeflow.go._generated.api.dataset_generators.delete_dataset_generator import (
    asyncio as delete_dataset_generator_asyncio,
)
from latticeflow.go._generated.api.dataset_generators.delete_dataset_generator import (
    sync as delete_dataset_generator_sync,
)
from latticeflow.go._generated.api.dataset_generators.generate_dataset import (
    asyncio as generate_dataset_asyncio,
)
from latticeflow.go._generated.api.dataset_generators.generate_dataset import (
    sync as generate_dataset_sync,
)
from latticeflow.go._generated.api.dataset_generators.get_dataset_generator import (
    asyncio as get_dataset_generator_asyncio,
)
from latticeflow.go._generated.api.dataset_generators.get_dataset_generator import (
    sync as get_dataset_generator_sync,
)
from latticeflow.go._generated.api.dataset_generators.get_dataset_generators import (
    asyncio as get_dataset_generators_asyncio,
)
from latticeflow.go._generated.api.dataset_generators.get_dataset_generators import (
    sync as get_dataset_generators_sync,
)
from latticeflow.go._generated.api.dataset_generators.preview_dataset_generation import (
    asyncio as preview_dataset_generation_asyncio,
)
from latticeflow.go._generated.api.dataset_generators.preview_dataset_generation import (
    sync as preview_dataset_generation_sync,
)
from latticeflow.go._generated.api.dataset_generators.update_dataset_generator import (
    asyncio as update_dataset_generator_asyncio,
)
from latticeflow.go._generated.api.dataset_generators.update_dataset_generator import (
    sync as update_dataset_generator_sync,
)
from latticeflow.go._generated.models.model import DatasetData
from latticeflow.go._generated.models.model import DatasetGenerationRequest
from latticeflow.go._generated.models.model import DatasetGenerator
from latticeflow.go._generated.models.model import Error
from latticeflow.go._generated.models.model import GeneratedDataset
from latticeflow.go._generated.models.model import StoredDataset
from latticeflow.go._generated.models.model import StoredDatasetGenerator
from latticeflow.go._generated.models.model import StoredDatasetGenerators
from latticeflow.go._generated.models.model import Success
from latticeflow.go._generated.types import UNSET
from latticeflow.go._generated.types import Unset
from latticeflow.go.extensions.resources.dataset_generators import (
    AsyncDatasetGeneratorsResource as AsyncBaseModule,
)
from latticeflow.go.extensions.resources.dataset_generators import (
    DatasetGeneratorsResource as BaseModule,
)
from latticeflow.go.types import ApiError


class DatasetGeneratorsResource(BaseModule):
    def preview_dataset_generation(
        self, dataset_generator_id: str, body: DatasetGenerationRequest
    ) -> DatasetData:
        """Preview dataset generation

         Preview dataset generation without creating a new dataset.

        Args:
            dataset_generator_id (str):
            body (DatasetGenerationRequest):
        """
        with self._base.get_client() as client:
            response = preview_dataset_generation_sync(
                dataset_generator_id=dataset_generator_id, body=body, client=client
            )
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    def get_dataset_generators(
        self, *, key: Union[Unset, str] = UNSET
    ) -> StoredDatasetGenerators:
        """Get all dataset generators

         Get all available dataset generators.

        Args:
            key (Union[Unset, str]):
        """
        with self._base.get_client() as client:
            response = get_dataset_generators_sync(client=client, key=key)
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    def update_dataset_generator(
        self, dataset_generator_id: str, body: DatasetGenerator
    ) -> StoredDatasetGenerator:
        """Update a dataset generator

         Update a dataset generator.

        Args:
            dataset_generator_id (str):
            body (DatasetGenerator):
        """
        with self._base.get_client() as client:
            response = update_dataset_generator_sync(
                dataset_generator_id=dataset_generator_id, body=body, client=client
            )
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    def delete_dataset_generator(self, dataset_generator_id: str) -> Success:
        """Delete a dataset generator

        Args:
            dataset_generator_id (str):
        """
        with self._base.get_client() as client:
            response = delete_dataset_generator_sync(
                dataset_generator_id=dataset_generator_id, client=client
            )
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    def generate_dataset(
        self, dataset_generator_id: str, body: GeneratedDataset
    ) -> StoredDataset:
        """Generate a dataset

         Generate a dataset using a dataset generator.

        Args:
            dataset_generator_id (str):
            body (GeneratedDataset):
        """
        with self._base.get_client() as client:
            response = generate_dataset_sync(
                dataset_generator_id=dataset_generator_id, body=body, client=client
            )
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    def create_dataset_generator(
        self, body: DatasetGenerator
    ) -> StoredDatasetGenerator:
        """Create a dataset generator

         Create a new dataset generator.

        Args:
            body (DatasetGenerator):
        """
        with self._base.get_client() as client:
            response = create_dataset_generator_sync(body=body, client=client)
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    def get_dataset_generator(
        self, dataset_generator_id: str
    ) -> StoredDatasetGenerator:
        """Get a dataset generator

         Get information about a dataset generator.

        Args:
            dataset_generator_id (str):
        """
        with self._base.get_client() as client:
            response = get_dataset_generator_sync(
                dataset_generator_id=dataset_generator_id, client=client
            )
            if isinstance(response, Error):
                raise ApiError(response)
            return response


class AsyncDatasetGeneratorsResource(AsyncBaseModule):
    async def preview_dataset_generation(
        self, dataset_generator_id: str, body: DatasetGenerationRequest
    ) -> DatasetData:
        """Preview dataset generation

         Preview dataset generation without creating a new dataset.

        Args:
            dataset_generator_id (str):
            body (DatasetGenerationRequest):
        """
        with self._base.get_client() as client:
            response = await preview_dataset_generation_asyncio(
                dataset_generator_id=dataset_generator_id, body=body, client=client
            )
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    async def get_dataset_generators(
        self, *, key: Union[Unset, str] = UNSET
    ) -> StoredDatasetGenerators:
        """Get all dataset generators

         Get all available dataset generators.

        Args:
            key (Union[Unset, str]):
        """
        with self._base.get_client() as client:
            response = await get_dataset_generators_asyncio(client=client, key=key)
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    async def update_dataset_generator(
        self, dataset_generator_id: str, body: DatasetGenerator
    ) -> StoredDatasetGenerator:
        """Update a dataset generator

         Update a dataset generator.

        Args:
            dataset_generator_id (str):
            body (DatasetGenerator):
        """
        with self._base.get_client() as client:
            response = await update_dataset_generator_asyncio(
                dataset_generator_id=dataset_generator_id, body=body, client=client
            )
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    async def delete_dataset_generator(self, dataset_generator_id: str) -> Success:
        """Delete a dataset generator

        Args:
            dataset_generator_id (str):
        """
        with self._base.get_client() as client:
            response = await delete_dataset_generator_asyncio(
                dataset_generator_id=dataset_generator_id, client=client
            )
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    async def generate_dataset(
        self, dataset_generator_id: str, body: GeneratedDataset
    ) -> StoredDataset:
        """Generate a dataset

         Generate a dataset using a dataset generator.

        Args:
            dataset_generator_id (str):
            body (GeneratedDataset):
        """
        with self._base.get_client() as client:
            response = await generate_dataset_asyncio(
                dataset_generator_id=dataset_generator_id, body=body, client=client
            )
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    async def create_dataset_generator(
        self, body: DatasetGenerator
    ) -> StoredDatasetGenerator:
        """Create a dataset generator

         Create a new dataset generator.

        Args:
            body (DatasetGenerator):
        """
        with self._base.get_client() as client:
            response = await create_dataset_generator_asyncio(body=body, client=client)
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    async def get_dataset_generator(
        self, dataset_generator_id: str
    ) -> StoredDatasetGenerator:
        """Get a dataset generator

         Get information about a dataset generator.

        Args:
            dataset_generator_id (str):
        """
        with self._base.get_client() as client:
            response = await get_dataset_generator_asyncio(
                dataset_generator_id=dataset_generator_id, client=client
            )
            if isinstance(response, Error):
                raise ApiError(response)
            return response
