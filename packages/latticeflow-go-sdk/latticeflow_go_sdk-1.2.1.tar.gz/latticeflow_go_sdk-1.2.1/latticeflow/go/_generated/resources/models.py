from __future__ import annotations

from typing import Union

from latticeflow.go._generated.api.models.check_model_connection import (
    asyncio as check_model_connection_asyncio,
)
from latticeflow.go._generated.api.models.check_model_connection import (
    sync as check_model_connection_sync,
)
from latticeflow.go._generated.api.models.create_model import (
    asyncio as create_model_asyncio,
)
from latticeflow.go._generated.api.models.create_model import sync as create_model_sync
from latticeflow.go._generated.api.models.delete_model import (
    asyncio as delete_model_asyncio,
)
from latticeflow.go._generated.api.models.delete_model import sync as delete_model_sync
from latticeflow.go._generated.api.models.get_model import asyncio as get_model_asyncio
from latticeflow.go._generated.api.models.get_model import sync as get_model_sync
from latticeflow.go._generated.api.models.get_model_provider import (
    asyncio as get_model_provider_asyncio,
)
from latticeflow.go._generated.api.models.get_model_provider import (
    sync as get_model_provider_sync,
)
from latticeflow.go._generated.api.models.get_model_providers import (
    asyncio as get_model_providers_asyncio,
)
from latticeflow.go._generated.api.models.get_model_providers import (
    sync as get_model_providers_sync,
)
from latticeflow.go._generated.api.models.get_models import (
    asyncio as get_models_asyncio,
)
from latticeflow.go._generated.api.models.get_models import sync as get_models_sync
from latticeflow.go._generated.api.models.run_model_inference import (
    asyncio as run_model_inference_asyncio,
)
from latticeflow.go._generated.api.models.run_model_inference import (
    sync as run_model_inference_sync,
)
from latticeflow.go._generated.api.models.transform_input_model import (
    asyncio as transform_input_model_asyncio,
)
from latticeflow.go._generated.api.models.transform_input_model import (
    sync as transform_input_model_sync,
)
from latticeflow.go._generated.api.models.transform_output_model import (
    asyncio as transform_output_model_asyncio,
)
from latticeflow.go._generated.api.models.transform_output_model import (
    sync as transform_output_model_sync,
)
from latticeflow.go._generated.api.models.update_model import (
    asyncio as update_model_asyncio,
)
from latticeflow.go._generated.api.models.update_model import sync as update_model_sync
from latticeflow.go._generated.models.model import ConnectionCheckResult
from latticeflow.go._generated.models.model import Error
from latticeflow.go._generated.models.model import Model
from latticeflow.go._generated.models.model import ModelAdapterInput
from latticeflow.go._generated.models.model import ModelAdapterOutput
from latticeflow.go._generated.models.model import ModelProvider
from latticeflow.go._generated.models.model import ModelProviders
from latticeflow.go._generated.models.model import RawModelInput
from latticeflow.go._generated.models.model import RawModelOutput
from latticeflow.go._generated.models.model import StoredModel
from latticeflow.go._generated.models.model import StoredModels
from latticeflow.go._generated.models.model import Success
from latticeflow.go._generated.types import UNSET
from latticeflow.go._generated.types import Unset
from latticeflow.go.extensions.resources.models import (
    AsyncModelsResource as AsyncBaseModule,
)
from latticeflow.go.extensions.resources.models import ModelsResource as BaseModule
from latticeflow.go.types import ApiError


class ModelsResource(BaseModule):
    def run_model_inference(self, model_id: str, body: RawModelInput) -> RawModelOutput:
        """Sends a raw model input to the model and request it to run inference.

         Use this API to send a prompt to the model. No transformation of the input or output will be
        performed by any model adapter.

        Args:
            model_id (str):
            body (RawModelInput): A generic raw model input.
        """
        with self._base.get_client() as client:
            response = run_model_inference_sync(
                model_id=model_id, body=body, client=client
            )
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    def transform_output_model(
        self, model_id: str, body: RawModelOutput
    ) -> ModelAdapterOutput:
        """Transforms the given model output to the LatticeFlow AIGO output format.

         This API attempts to transform a model output to the format defined by AIGO.

        This API is intended to be used for probing the correctness of the model adapter.

        Nothing is sent to the model in the process.

        Args:
            model_id (str):
            body (RawModelOutput): A raw model response.
        """
        with self._base.get_client() as client:
            response = transform_output_model_sync(
                model_id=model_id, body=body, client=client
            )
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    def get_model(self, model_id: str) -> StoredModel:
        """Get a model

        Args:
            model_id (str):
        """
        with self._base.get_client() as client:
            response = get_model_sync(model_id=model_id, client=client)
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    def check_model_connection(self, model_id: str) -> ConnectionCheckResult:
        """Check the connection to the model.

         Use this API to check the basic connectivity and authentication to the model.

        The API will make an empty, possibly malformed, request to the model. The check
        is considered successful if the model responds with any 2xx or 4xx HTTP response,
        except for 401 and 403 - these are considered as errors in the authenticaiton to the
        model (e.g. due to invalid API key, etc.).

        Args:
            model_id (str):
        """
        with self._base.get_client() as client:
            response = check_model_connection_sync(model_id=model_id, client=client)
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    def get_model_providers(self) -> ModelProviders:
        """Get all model providers"""
        with self._base.get_client() as client:
            response = get_model_providers_sync(client=client)
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    def update_model(self, model_id: str, body: Model) -> StoredModel:
        """Update a model

        Args:
            model_id (str):
            body (Model): Representation of a publicly accessible model.
        """
        with self._base.get_client() as client:
            response = update_model_sync(model_id=model_id, body=body, client=client)
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    def transform_input_model(
        self, model_id: str, body: ModelAdapterInput
    ) -> RawModelInput:
        """Transforms the given input so it is suitable for use with a model.

         This API attempts to transform a model input formatted in the AIGO format to
        the format required by the model using a model adapter.

        This API is intended to be used for probing the correctness of the model adapter.

        Nothing is sent to the model in the process.

        Args:
            model_id (str):
            body (ModelAdapterInput): Model input represented in the LatticeFlow AIGO format.
        """
        with self._base.get_client() as client:
            response = transform_input_model_sync(
                model_id=model_id, body=body, client=client
            )
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    def get_models(self, *, key: Union[Unset, str] = UNSET) -> StoredModels:
        """Get all models

        Args:
            key (Union[Unset, str]):
        """
        with self._base.get_client() as client:
            response = get_models_sync(client=client, key=key)
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    def delete_model(self, model_id: str) -> Success:
        """Delete a model

        Args:
            model_id (str):
        """
        with self._base.get_client() as client:
            response = delete_model_sync(model_id=model_id, client=client)
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    def create_model(self, body: Model) -> StoredModel:
        """Create a model

        Args:
            body (Model): Representation of a publicly accessible model.
        """
        with self._base.get_client() as client:
            response = create_model_sync(body=body, client=client)
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    def get_model_provider(self, provider_id: str) -> ModelProvider:
        """Get a model provider

        Args:
            provider_id (str):
        """
        with self._base.get_client() as client:
            response = get_model_provider_sync(provider_id=provider_id, client=client)
            if isinstance(response, Error):
                raise ApiError(response)
            return response


class AsyncModelsResource(AsyncBaseModule):
    async def run_model_inference(
        self, model_id: str, body: RawModelInput
    ) -> RawModelOutput:
        """Sends a raw model input to the model and request it to run inference.

         Use this API to send a prompt to the model. No transformation of the input or output will be
        performed by any model adapter.

        Args:
            model_id (str):
            body (RawModelInput): A generic raw model input.
        """
        with self._base.get_client() as client:
            response = await run_model_inference_asyncio(
                model_id=model_id, body=body, client=client
            )
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    async def transform_output_model(
        self, model_id: str, body: RawModelOutput
    ) -> ModelAdapterOutput:
        """Transforms the given model output to the LatticeFlow AIGO output format.

         This API attempts to transform a model output to the format defined by AIGO.

        This API is intended to be used for probing the correctness of the model adapter.

        Nothing is sent to the model in the process.

        Args:
            model_id (str):
            body (RawModelOutput): A raw model response.
        """
        with self._base.get_client() as client:
            response = await transform_output_model_asyncio(
                model_id=model_id, body=body, client=client
            )
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    async def get_model(self, model_id: str) -> StoredModel:
        """Get a model

        Args:
            model_id (str):
        """
        with self._base.get_client() as client:
            response = await get_model_asyncio(model_id=model_id, client=client)
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    async def check_model_connection(self, model_id: str) -> ConnectionCheckResult:
        """Check the connection to the model.

         Use this API to check the basic connectivity and authentication to the model.

        The API will make an empty, possibly malformed, request to the model. The check
        is considered successful if the model responds with any 2xx or 4xx HTTP response,
        except for 401 and 403 - these are considered as errors in the authenticaiton to the
        model (e.g. due to invalid API key, etc.).

        Args:
            model_id (str):
        """
        with self._base.get_client() as client:
            response = await check_model_connection_asyncio(
                model_id=model_id, client=client
            )
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    async def get_model_providers(self) -> ModelProviders:
        """Get all model providers"""
        with self._base.get_client() as client:
            response = await get_model_providers_asyncio(client=client)
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    async def update_model(self, model_id: str, body: Model) -> StoredModel:
        """Update a model

        Args:
            model_id (str):
            body (Model): Representation of a publicly accessible model.
        """
        with self._base.get_client() as client:
            response = await update_model_asyncio(
                model_id=model_id, body=body, client=client
            )
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    async def transform_input_model(
        self, model_id: str, body: ModelAdapterInput
    ) -> RawModelInput:
        """Transforms the given input so it is suitable for use with a model.

         This API attempts to transform a model input formatted in the AIGO format to
        the format required by the model using a model adapter.

        This API is intended to be used for probing the correctness of the model adapter.

        Nothing is sent to the model in the process.

        Args:
            model_id (str):
            body (ModelAdapterInput): Model input represented in the LatticeFlow AIGO format.
        """
        with self._base.get_client() as client:
            response = await transform_input_model_asyncio(
                model_id=model_id, body=body, client=client
            )
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    async def get_models(self, *, key: Union[Unset, str] = UNSET) -> StoredModels:
        """Get all models

        Args:
            key (Union[Unset, str]):
        """
        with self._base.get_client() as client:
            response = await get_models_asyncio(client=client, key=key)
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    async def delete_model(self, model_id: str) -> Success:
        """Delete a model

        Args:
            model_id (str):
        """
        with self._base.get_client() as client:
            response = await delete_model_asyncio(model_id=model_id, client=client)
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    async def create_model(self, body: Model) -> StoredModel:
        """Create a model

        Args:
            body (Model): Representation of a publicly accessible model.
        """
        with self._base.get_client() as client:
            response = await create_model_asyncio(body=body, client=client)
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    async def get_model_provider(self, provider_id: str) -> ModelProvider:
        """Get a model provider

        Args:
            provider_id (str):
        """
        with self._base.get_client() as client:
            response = await get_model_provider_asyncio(
                provider_id=provider_id, client=client
            )
            if isinstance(response, Error):
                raise ApiError(response)
            return response
