from __future__ import annotations

from typing import TYPE_CHECKING

from latticeflow.go.models import Error
from latticeflow.go.models import StoredTenant
from latticeflow.go.models import StoredUser
from latticeflow.go.models import Success
from latticeflow.go.models import Users
from latticeflow.go.types import ApiError


if TYPE_CHECKING:
    from latticeflow.go import AsyncClient
    from latticeflow.go import Client


class TenantsResource:
    def __init__(self, base_client: Client) -> None:
        self._base = base_client

    def get_tenant_by_alias(self, alias: str) -> StoredTenant:
        """Get the Tenant with the given alias.

        Args:
            alias: The alias of the Tenant.

        Raises:
            ApiError: If there is no Tenant with the given alias.
        """
        for tenant in self._base.tenants.get_tenants().tenants:
            if tenant.alias == alias:
                return tenant

        raise ApiError(Error(message=f"Tenant with alias '{alias}' not found."))

    def delete_tenant_by_alias(self, alias: str) -> Success:
        """Delete the Tenant with the given alias.

        Args:
            alias: The alias of the Tenant.

        Raises:
            ApiError: If there is no Tenant with the given alias.
            ApiError: If the deletion of the Tenant with the given alias fails.
        """
        return self._base.tenants.delete_tenant(self.get_tenant_by_alias(alias).id)

    def get_all_tenant_users_by_alias(self, alias: str) -> Users:
        """Gets all users for the Tenant with the given alias.

        Args:
            alias: The alias of the Tenant.

        Raises:
            ApiError: If there is no Tenant with the given alias.
        """
        return self._base.tenants.get_all_users_for_tenant(
            self.get_tenant_by_alias(alias).id
        )

    def get_tenant_user_by_email(self, email: str, tenant_alias: str) -> StoredUser:
        """Gets the User with the given email for the Tenant with the given alias.

        Args:
            email: The email of the user.
            tenant_alias: The alias of the Tenant.

        Raises:
            ApiError: If there is no Tenant with the given tenant_alias.
            ApiError: If there is no User with the given email for the given Tenant.
        """
        stored_users = self._base.tenants.get_all_users_for_tenant(
            self.get_tenant_by_alias(tenant_alias).id
        )
        for stored_user in stored_users.users:
            if stored_user.email == email:
                return stored_user

        raise ApiError(
            Error(
                message=(
                    f"User with email '{email}' for tenant with alias '{tenant_alias}' "
                    "not found."
                )
            )
        )


class AsyncTenantsResource:
    def __init__(self, base_client: AsyncClient) -> None:
        self._base = base_client

    async def get_tenant_by_alias(self, alias: str) -> StoredTenant:
        """Get the Tenant with the given alias.

        Args:
            alias: The alias of the Tenant.

        Raises:
            ApiError: If there is no Tenant with the given alias.
        """
        for tenant in (await self._base.tenants.get_tenants()).tenants:
            if tenant.alias == alias:
                return tenant

        raise ApiError(Error(message=f"Tenant with alias '{alias}' not found."))

    async def delete_tenant_by_alias(self, alias: str) -> Success:
        """Delete the Tenant with the given alias.

        Args:
            alias: The alias of the Tenant.

        Raises:
            ApiError: If there is no Tenant with the given alias.
            ApiError: If the deletion of the Tenant with the given alias fails.
        """
        return await self._base.tenants.delete_tenant(
            (await self.get_tenant_by_alias(alias)).id
        )

    async def get_all_tenant_users_by_alias(self, alias: str) -> Users:
        """Gets all users for the Tenant with the given alias.

        Args:
            alias: The alias of the Tenant.

        Raises:
            ApiError: If there is no Tenant with the given alias.
        """
        return await self._base.tenants.get_all_users_for_tenant(
            (await self.get_tenant_by_alias(alias)).id
        )

    async def get_tenant_user_by_email(
        self, email: str, tenant_alias: str
    ) -> StoredUser:
        """Gets the User with the given email for the Tenant with the given alias.

        Args:
            email: The email of the user.
            tenant_alias: The alias of the Tenant.

        Raises:
            ApiError: If there is no Tenant with the given tenant_alias.
            ApiError: If there is no User with the given email for the given Tenant.
        """
        stored_users = await self._base.tenants.get_all_users_for_tenant(
            (await self.get_tenant_by_alias(tenant_alias)).id
        )
        for stored_user in stored_users.users:
            if stored_user.email == email:
                return stored_user

        raise ApiError(
            Error(
                message=(
                    f"User with email '{email}' for tenant with alias '{tenant_alias}' "
                    "not found."
                )
            )
        )
