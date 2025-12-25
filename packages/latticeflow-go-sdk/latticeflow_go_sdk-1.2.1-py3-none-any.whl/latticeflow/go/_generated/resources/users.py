from __future__ import annotations

from latticeflow.go._generated.api.users.create_user import (
    asyncio as create_user_asyncio,
)
from latticeflow.go._generated.api.users.create_user import sync as create_user_sync
from latticeflow.go._generated.api.users.get_user import asyncio as get_user_asyncio
from latticeflow.go._generated.api.users.get_user import sync as get_user_sync
from latticeflow.go._generated.api.users.get_users import asyncio as get_users_asyncio
from latticeflow.go._generated.api.users.get_users import sync as get_users_sync
from latticeflow.go._generated.api.users.reset_user_credential import (
    asyncio as reset_user_credential_asyncio,
)
from latticeflow.go._generated.api.users.reset_user_credential import (
    sync as reset_user_credential_sync,
)
from latticeflow.go._generated.api.users.set_user_credential import (
    asyncio as set_user_credential_asyncio,
)
from latticeflow.go._generated.api.users.set_user_credential import (
    sync as set_user_credential_sync,
)
from latticeflow.go._generated.api.users.update_user import (
    asyncio as update_user_asyncio,
)
from latticeflow.go._generated.api.users.update_user import sync as update_user_sync
from latticeflow.go._generated.models.model import Error
from latticeflow.go._generated.models.model import PasswordUserCredential
from latticeflow.go._generated.models.model import ResetUserCredentialAction
from latticeflow.go._generated.models.model import StoredUser
from latticeflow.go._generated.models.model import Success
from latticeflow.go._generated.models.model import User
from latticeflow.go._generated.models.model import Users
from latticeflow.go.extensions.resources.users import (
    AsyncUsersResource as AsyncBaseModule,
)
from latticeflow.go.extensions.resources.users import UsersResource as BaseModule
from latticeflow.go.types import ApiError


class UsersResource(BaseModule):
    def get_user(self, user_id: str) -> StoredUser:
        """Get a user

        Args:
            user_id (str):
        """
        with self._base.get_client() as client:
            response = get_user_sync(user_id=user_id, client=client)
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    def get_users(self) -> Users:
        """Get all users"""
        with self._base.get_client() as client:
            response = get_users_sync(client=client)
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    def create_user(self, body: User) -> StoredUser:
        """Create a user

        Args:
            body (User):
        """
        with self._base.get_client() as client:
            response = create_user_sync(body=body, client=client)
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    def reset_user_credential(
        self, user_id: str, body: ResetUserCredentialAction
    ) -> PasswordUserCredential:
        """Reset a user credential.

        Args:
            user_id (str):
            body (ResetUserCredentialAction):
        """
        with self._base.get_client() as client:
            response = reset_user_credential_sync(
                user_id=user_id, body=body, client=client
            )
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    def set_user_credential(
        self, user_id: str, body: PasswordUserCredential
    ) -> Success:
        """Set a user credential.

        Args:
            user_id (str):
            body (PasswordUserCredential):
        """
        with self._base.get_client() as client:
            response = set_user_credential_sync(
                user_id=user_id, body=body, client=client
            )
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    def update_user(self, user_id: str, body: User) -> StoredUser:
        """Update a user.

        Args:
            user_id (str):
            body (User):
        """
        with self._base.get_client() as client:
            response = update_user_sync(user_id=user_id, body=body, client=client)
            if isinstance(response, Error):
                raise ApiError(response)
            return response


class AsyncUsersResource(AsyncBaseModule):
    async def get_user(self, user_id: str) -> StoredUser:
        """Get a user

        Args:
            user_id (str):
        """
        with self._base.get_client() as client:
            response = await get_user_asyncio(user_id=user_id, client=client)
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    async def get_users(self) -> Users:
        """Get all users"""
        with self._base.get_client() as client:
            response = await get_users_asyncio(client=client)
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    async def create_user(self, body: User) -> StoredUser:
        """Create a user

        Args:
            body (User):
        """
        with self._base.get_client() as client:
            response = await create_user_asyncio(body=body, client=client)
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    async def reset_user_credential(
        self, user_id: str, body: ResetUserCredentialAction
    ) -> PasswordUserCredential:
        """Reset a user credential.

        Args:
            user_id (str):
            body (ResetUserCredentialAction):
        """
        with self._base.get_client() as client:
            response = await reset_user_credential_asyncio(
                user_id=user_id, body=body, client=client
            )
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    async def set_user_credential(
        self, user_id: str, body: PasswordUserCredential
    ) -> Success:
        """Set a user credential.

        Args:
            user_id (str):
            body (PasswordUserCredential):
        """
        with self._base.get_client() as client:
            response = await set_user_credential_asyncio(
                user_id=user_id, body=body, client=client
            )
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    async def update_user(self, user_id: str, body: User) -> StoredUser:
        """Update a user.

        Args:
            user_id (str):
            body (User):
        """
        with self._base.get_client() as client:
            response = await update_user_asyncio(
                user_id=user_id, body=body, client=client
            )
            if isinstance(response, Error):
                raise ApiError(response)
            return response
