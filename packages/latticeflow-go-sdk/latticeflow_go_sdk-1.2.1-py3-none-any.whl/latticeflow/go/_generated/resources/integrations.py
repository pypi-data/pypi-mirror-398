from __future__ import annotations

from typing import Union

from latticeflow.go._generated.api.integrations.get_integration import (
    asyncio as get_integration_asyncio,
)
from latticeflow.go._generated.api.integrations.get_integration import (
    sync as get_integration_sync,
)
from latticeflow.go._generated.api.integrations.get_integrations import (
    asyncio as get_integrations_asyncio,
)
from latticeflow.go._generated.api.integrations.get_integrations import (
    sync as get_integrations_sync,
)
from latticeflow.go._generated.api.integrations.test_integration import (
    asyncio as test_integration_asyncio,
)
from latticeflow.go._generated.api.integrations.test_integration import (
    sync as test_integration_sync,
)
from latticeflow.go._generated.api.integrations.update_integration import (
    asyncio as update_integration_asyncio,
)
from latticeflow.go._generated.api.integrations.update_integration import (
    sync as update_integration_sync,
)
from latticeflow.go._generated.api.integrations.update_open_ai_integration import (
    asyncio as update_open_ai_integration_asyncio,
)
from latticeflow.go._generated.api.integrations.update_open_ai_integration import (
    sync as update_open_ai_integration_sync,
)
from latticeflow.go._generated.api.integrations.update_zenguard_integration import (
    asyncio as update_zenguard_integration_asyncio,
)
from latticeflow.go._generated.api.integrations.update_zenguard_integration import (
    sync as update_zenguard_integration_sync,
)
from latticeflow.go._generated.models.model import ConnectionCheckResult
from latticeflow.go._generated.models.model import Error
from latticeflow.go._generated.models.model import Integration
from latticeflow.go._generated.models.model import IntegrationDatasetProviderId
from latticeflow.go._generated.models.model import IntegrationModelProviderId
from latticeflow.go._generated.models.model import OpenAIIntegration
from latticeflow.go._generated.models.model import StoredIntegration
from latticeflow.go._generated.models.model import StoredIntegrations
from latticeflow.go._generated.models.model import ZenguardIntegration
from latticeflow.go.base import BaseClient
from latticeflow.go.types import ApiError


class IntegrationsResource:
    def __init__(self, base_client: BaseClient) -> None:
        self._base = base_client

    def get_integrations(self) -> StoredIntegrations:
        """Information about all integrations"""
        with self._base.get_client() as client:
            response = get_integrations_sync(client=client)
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    def update_open_ai_integration(self, body: OpenAIIntegration) -> StoredIntegration:
        """Update the OpenAI integration.

        Args:
            body (OpenAIIntegration): The OpenAI integration configuration object.
        """
        with self._base.get_client() as client:
            response = update_open_ai_integration_sync(body=body, client=client)
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    def get_integration(self, integration_id: str) -> StoredIntegration:
        """Get integration info.

        Args:
            integration_id (str):
        """
        with self._base.get_client() as client:
            response = get_integration_sync(
                integration_id=integration_id, client=client
            )
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    def test_integration(
        self,
        integration_id: Union[IntegrationDatasetProviderId, IntegrationModelProviderId],
    ) -> ConnectionCheckResult:
        """Test the connection to the integration

        Args:
            integration_id (Union[IntegrationDatasetProviderId, IntegrationModelProviderId]): The ids
                for all integrations the system supports.
        """
        with self._base.get_client() as client:
            response = test_integration_sync(
                integration_id=integration_id, client=client
            )
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    def update_zenguard_integration(
        self, body: ZenguardIntegration
    ) -> StoredIntegration:
        """Update the Zenguard integration.

        Args:
            body (ZenguardIntegration): The Zenguard integration configuration object.
        """
        with self._base.get_client() as client:
            response = update_zenguard_integration_sync(body=body, client=client)
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    def update_integration(
        self, integration_id: str, body: Integration
    ) -> StoredIntegration:
        """Update the integrations that have simple connection info(only api_key).

        Args:
            integration_id (str):
            body (Integration): Basic integration information shared between most integrations.
        """
        with self._base.get_client() as client:
            response = update_integration_sync(
                integration_id=integration_id, body=body, client=client
            )
            if isinstance(response, Error):
                raise ApiError(response)
            return response


class AsyncIntegrationsResource:
    def __init__(self, base_client: BaseClient) -> None:
        self._base = base_client

    async def get_integrations(self) -> StoredIntegrations:
        """Information about all integrations"""
        with self._base.get_client() as client:
            response = await get_integrations_asyncio(client=client)
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    async def update_open_ai_integration(
        self, body: OpenAIIntegration
    ) -> StoredIntegration:
        """Update the OpenAI integration.

        Args:
            body (OpenAIIntegration): The OpenAI integration configuration object.
        """
        with self._base.get_client() as client:
            response = await update_open_ai_integration_asyncio(
                body=body, client=client
            )
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    async def get_integration(self, integration_id: str) -> StoredIntegration:
        """Get integration info.

        Args:
            integration_id (str):
        """
        with self._base.get_client() as client:
            response = await get_integration_asyncio(
                integration_id=integration_id, client=client
            )
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    async def test_integration(
        self,
        integration_id: Union[IntegrationDatasetProviderId, IntegrationModelProviderId],
    ) -> ConnectionCheckResult:
        """Test the connection to the integration

        Args:
            integration_id (Union[IntegrationDatasetProviderId, IntegrationModelProviderId]): The ids
                for all integrations the system supports.
        """
        with self._base.get_client() as client:
            response = await test_integration_asyncio(
                integration_id=integration_id, client=client
            )
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    async def update_zenguard_integration(
        self, body: ZenguardIntegration
    ) -> StoredIntegration:
        """Update the Zenguard integration.

        Args:
            body (ZenguardIntegration): The Zenguard integration configuration object.
        """
        with self._base.get_client() as client:
            response = await update_zenguard_integration_asyncio(
                body=body, client=client
            )
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    async def update_integration(
        self, integration_id: str, body: Integration
    ) -> StoredIntegration:
        """Update the integrations that have simple connection info(only api_key).

        Args:
            integration_id (str):
            body (Integration): Basic integration information shared between most integrations.
        """
        with self._base.get_client() as client:
            response = await update_integration_asyncio(
                integration_id=integration_id, body=body, client=client
            )
            if isinstance(response, Error):
                raise ApiError(response)
            return response
