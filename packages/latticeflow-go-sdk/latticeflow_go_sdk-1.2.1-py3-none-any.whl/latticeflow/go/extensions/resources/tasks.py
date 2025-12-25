from __future__ import annotations

from typing import TYPE_CHECKING

from latticeflow.go.models import Error
from latticeflow.go.models import StoredTask
from latticeflow.go.models import Success
from latticeflow.go.types import ApiError


if TYPE_CHECKING:
    from latticeflow.go import AsyncClient
    from latticeflow.go import Client


class TasksResource:
    def __init__(self, base_client: Client) -> None:
        self._base = base_client

    def get_task_by_key(self, key: str) -> StoredTask:
        """Get the Task with the given key.

        Args:
            key: The key of the Task.

        Raises:
            ApiError: If there is no Task with the given key.
        """
        tasks = self._base.tasks.get_tasks(key=key).tasks
        if not tasks:
            raise ApiError(Error(message=f"Task with key '{key}' not found."))

        return tasks[0]

    def delete_task_by_key(self, key: str, *, delete_evaluations: bool) -> Success:
        """Delete the Task by the given key.

        Args:
            key: The key of the Task to be deleted.

        Raises:
            ApiError: If there is no Task with the given key.
            ApiError: If the deletion of the Task fails.
        """
        return self._base.tasks.delete_task(
            self._base.tasks.get_task_by_key(key=key).id,
            delete_evaluations=delete_evaluations,
        )


class AsyncTasksResource:
    def __init__(self, base_client: AsyncClient) -> None:
        self._base = base_client

    async def get_task_by_key(self, key: str) -> StoredTask:
        """Get the Task with the given key.

        Args:
            key: The key of the Task.

        Raises:
            ApiError: If there is no Task with the given key.
        """
        tasks = (await self._base.tasks.get_tasks(key=key)).tasks
        if not tasks:
            raise ApiError(Error(message=f"Task with key '{key}' not found."))

        return tasks[0]

    async def delete_task_by_key(
        self, key: str, *, delete_evaluations: bool
    ) -> Success:
        """Delete the Task by the given key.

        Args:
            key: The key of the Task to be deleted.

        Raises:
            ApiError: If there is no Task with the given key.
            ApiError: If the deletion of the Task fails.
        """
        return await self._base.tasks.delete_task(
            (await self._base.tasks.get_task_by_key(key=key)).id,
            delete_evaluations=delete_evaluations,
        )
