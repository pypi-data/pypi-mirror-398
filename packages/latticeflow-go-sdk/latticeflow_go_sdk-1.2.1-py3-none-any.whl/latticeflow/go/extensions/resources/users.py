from __future__ import annotations

from typing import TYPE_CHECKING

from latticeflow.go.models import Error
from latticeflow.go.models import StoredUser
from latticeflow.go.models import User
from latticeflow.go.types import ApiError


if TYPE_CHECKING:
    from latticeflow.go import AsyncClient
    from latticeflow.go import Client


class UsersResource:
    def __init__(self, base_client: Client) -> None:
        self._base = base_client

    def get_user_by_email(self, email: str) -> StoredUser:
        """Get the User with the given email.

        Args:
            email: The email of the User.

        Raises:
            ApiError: If there is no User with the given email.
        """
        for stored_user in self._base.users.get_users().users:
            if stored_user.email == email:
                return stored_user

        raise ApiError(Error(message=f"User with email '{email}' not found."))

    def update_user_status_by_email(self, email: str, enabled: bool) -> StoredUser:
        """Update the status of the User with the given email.

        Args:
            email: The email of the User.
            enabled: The status which the user should be set to (enabled/disabled).

        Raises:
            ApiError: If there is no User with the given email.
            ApiError: If the status of the User with the given email could not be changed.
        """
        stored_user = self.get_user_by_email(email)
        return self._base.users.update_user(
            stored_user.id,
            User.model_validate({**stored_user.model_dump(), "enabled": enabled}),
        )


class AsyncUsersResource:
    def __init__(self, base_client: AsyncClient) -> None:
        self._base = base_client

    async def get_user_by_email(self, email: str) -> StoredUser:
        """Get the User with the given email.

        Args:
            email: The email of the User.

        Raises:
            ApiError: If there is no User with the given email.
        """
        for stored_user in (await self._base.users.get_users()).users:
            if stored_user.email == email:
                return stored_user

        raise ApiError(Error(message=f"User with email '{email}' not found."))

    async def update_user_status_by_email(
        self, email: str, enabled: bool
    ) -> StoredUser:
        """Update the status of the User with the given email.

        Args:
            email: The email of the User.
            enabled: The status which the user should be set to (enabled/disabled).

        Raises:
            ApiError: If there is no User with the given email.
            ApiError: If the status of the User with the given email could not be changed.
        """
        stored_user = await self.get_user_by_email(email)
        return await self._base.users.update_user(
            stored_user.id,
            User.model_validate({**stored_user.model_dump(), "enabled": enabled}),
        )
