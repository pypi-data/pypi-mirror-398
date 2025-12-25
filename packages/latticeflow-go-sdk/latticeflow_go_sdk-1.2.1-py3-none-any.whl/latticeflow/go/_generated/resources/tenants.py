from __future__ import annotations

from latticeflow.go._generated.api.tenants.create_tenant import (
    asyncio as create_tenant_asyncio,
)
from latticeflow.go._generated.api.tenants.create_tenant import (
    sync as create_tenant_sync,
)
from latticeflow.go._generated.api.tenants.create_tenant_user import (
    asyncio as create_tenant_user_asyncio,
)
from latticeflow.go._generated.api.tenants.create_tenant_user import (
    sync as create_tenant_user_sync,
)
from latticeflow.go._generated.api.tenants.delete_tenant import (
    asyncio as delete_tenant_asyncio,
)
from latticeflow.go._generated.api.tenants.delete_tenant import (
    sync as delete_tenant_sync,
)
from latticeflow.go._generated.api.tenants.get_all_users_for_tenant import (
    asyncio as get_all_users_for_tenant_asyncio,
)
from latticeflow.go._generated.api.tenants.get_all_users_for_tenant import (
    sync as get_all_users_for_tenant_sync,
)
from latticeflow.go._generated.api.tenants.get_tenants import (
    asyncio as get_tenants_asyncio,
)
from latticeflow.go._generated.api.tenants.get_tenants import sync as get_tenants_sync
from latticeflow.go._generated.api.tenants.reset_tenant_user_credential import (
    asyncio as reset_tenant_user_credential_asyncio,
)
from latticeflow.go._generated.api.tenants.reset_tenant_user_credential import (
    sync as reset_tenant_user_credential_sync,
)
from latticeflow.go._generated.models.model import Error
from latticeflow.go._generated.models.model import PasswordUserCredential
from latticeflow.go._generated.models.model import ResetUserCredentialAction
from latticeflow.go._generated.models.model import StoredTenant
from latticeflow.go._generated.models.model import StoredTenants
from latticeflow.go._generated.models.model import StoredUser
from latticeflow.go._generated.models.model import Success
from latticeflow.go._generated.models.model import Tenant
from latticeflow.go._generated.models.model import User
from latticeflow.go._generated.models.model import Users
from latticeflow.go.extensions.resources.tenants import (
    AsyncTenantsResource as AsyncBaseModule,
)
from latticeflow.go.extensions.resources.tenants import TenantsResource as BaseModule
from latticeflow.go.types import ApiError


class TenantsResource(BaseModule):
    def get_all_users_for_tenant(self, tenant_id: str) -> Users:
        """Get all users for a tenant

        Args:
            tenant_id (str):
        """
        with self._base.get_client() as client:
            response = get_all_users_for_tenant_sync(tenant_id=tenant_id, client=client)
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    def create_tenant_user(self, tenant_id: str, body: User) -> StoredUser:
        """Create a user

        Args:
            tenant_id (str):
            body (User):
        """
        with self._base.get_client() as client:
            response = create_tenant_user_sync(
                tenant_id=tenant_id, body=body, client=client
            )
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    def delete_tenant(self, tenant_id: str) -> Success:
        """Delete a tenant by tenant ID

        Args:
            tenant_id (str):
        """
        with self._base.get_client() as client:
            response = delete_tenant_sync(tenant_id=tenant_id, client=client)
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    def get_tenants(self) -> StoredTenants:
        """Get all tenants"""
        with self._base.get_client() as client:
            response = get_tenants_sync(client=client)
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    def reset_tenant_user_credential(
        self, tenant_id: str, user_id: str, body: ResetUserCredentialAction
    ) -> PasswordUserCredential:
        """Reset a user credential.

        Args:
            tenant_id (str):
            user_id (str):
            body (ResetUserCredentialAction):
        """
        with self._base.get_client() as client:
            response = reset_tenant_user_credential_sync(
                tenant_id=tenant_id, user_id=user_id, body=body, client=client
            )
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    def create_tenant(self, body: Tenant) -> StoredTenant:
        """Create a tenant

        Args:
            body (Tenant):
        """
        with self._base.get_client() as client:
            response = create_tenant_sync(body=body, client=client)
            if isinstance(response, Error):
                raise ApiError(response)
            return response


class AsyncTenantsResource(AsyncBaseModule):
    async def get_all_users_for_tenant(self, tenant_id: str) -> Users:
        """Get all users for a tenant

        Args:
            tenant_id (str):
        """
        with self._base.get_client() as client:
            response = await get_all_users_for_tenant_asyncio(
                tenant_id=tenant_id, client=client
            )
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    async def create_tenant_user(self, tenant_id: str, body: User) -> StoredUser:
        """Create a user

        Args:
            tenant_id (str):
            body (User):
        """
        with self._base.get_client() as client:
            response = await create_tenant_user_asyncio(
                tenant_id=tenant_id, body=body, client=client
            )
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    async def delete_tenant(self, tenant_id: str) -> Success:
        """Delete a tenant by tenant ID

        Args:
            tenant_id (str):
        """
        with self._base.get_client() as client:
            response = await delete_tenant_asyncio(tenant_id=tenant_id, client=client)
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    async def get_tenants(self) -> StoredTenants:
        """Get all tenants"""
        with self._base.get_client() as client:
            response = await get_tenants_asyncio(client=client)
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    async def reset_tenant_user_credential(
        self, tenant_id: str, user_id: str, body: ResetUserCredentialAction
    ) -> PasswordUserCredential:
        """Reset a user credential.

        Args:
            tenant_id (str):
            user_id (str):
            body (ResetUserCredentialAction):
        """
        with self._base.get_client() as client:
            response = await reset_tenant_user_credential_asyncio(
                tenant_id=tenant_id, user_id=user_id, body=body, client=client
            )
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    async def create_tenant(self, body: Tenant) -> StoredTenant:
        """Create a tenant

        Args:
            body (Tenant):
        """
        with self._base.get_client() as client:
            response = await create_tenant_asyncio(body=body, client=client)
            if isinstance(response, Error):
                raise ApiError(response)
            return response
