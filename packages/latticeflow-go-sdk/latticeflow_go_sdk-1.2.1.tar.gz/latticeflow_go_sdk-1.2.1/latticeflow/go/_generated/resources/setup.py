from __future__ import annotations

from latticeflow.go._generated.api.setup.get_app_state import (
    asyncio as get_app_state_asyncio,
)
from latticeflow.go._generated.api.setup.get_app_state import sync as get_app_state_sync
from latticeflow.go._generated.api.setup.initial_setup import (
    asyncio as initial_setup_asyncio,
)
from latticeflow.go._generated.api.setup.initial_setup import sync as initial_setup_sync
from latticeflow.go._generated.models.model import Error
from latticeflow.go._generated.models.model import InitialSetupRequest
from latticeflow.go._generated.models.model import State
from latticeflow.go._generated.models.model import StoredUser
from latticeflow.go.base import BaseClient
from latticeflow.go.types import ApiError


class SetupResource:
    def __init__(self, base_client: BaseClient) -> None:
        self._base = base_client

    def get_app_state(self) -> State:
        """Get application state"""
        with self._base.get_client() as client:
            response = get_app_state_sync(client=client)
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    def initial_setup(self, body: InitialSetupRequest) -> StoredUser:
        """Initialize the application with an initial user.
        This endpoint is used during the initial setup process.

        Args:
            body (InitialSetupRequest):
        """
        with self._base.get_client() as client:
            response = initial_setup_sync(body=body, client=client)
            if isinstance(response, Error):
                raise ApiError(response)
            return response


class AsyncSetupResource:
    def __init__(self, base_client: BaseClient) -> None:
        self._base = base_client

    async def get_app_state(self) -> State:
        """Get application state"""
        with self._base.get_client() as client:
            response = await get_app_state_asyncio(client=client)
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    async def initial_setup(self, body: InitialSetupRequest) -> StoredUser:
        """Initialize the application with an initial user.
        This endpoint is used during the initial setup process.

        Args:
            body (InitialSetupRequest):
        """
        with self._base.get_client() as client:
            response = await initial_setup_asyncio(body=body, client=client)
            if isinstance(response, Error):
                raise ApiError(response)
            return response
