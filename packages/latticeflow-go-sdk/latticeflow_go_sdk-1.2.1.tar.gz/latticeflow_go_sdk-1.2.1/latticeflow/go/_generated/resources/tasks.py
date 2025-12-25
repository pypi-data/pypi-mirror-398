from __future__ import annotations

from typing import Union

from latticeflow.go._generated.api.tasks.create_task import (
    asyncio as create_task_asyncio,
)
from latticeflow.go._generated.api.tasks.create_task import sync as create_task_sync
from latticeflow.go._generated.api.tasks.delete_task import (
    asyncio as delete_task_asyncio,
)
from latticeflow.go._generated.api.tasks.delete_task import sync as delete_task_sync
from latticeflow.go._generated.api.tasks.get_task import asyncio as get_task_asyncio
from latticeflow.go._generated.api.tasks.get_task import sync as get_task_sync
from latticeflow.go._generated.api.tasks.get_tasks import asyncio as get_tasks_asyncio
from latticeflow.go._generated.api.tasks.get_tasks import sync as get_tasks_sync
from latticeflow.go._generated.api.tasks.test_task import asyncio as test_task_asyncio
from latticeflow.go._generated.api.tasks.test_task import sync as test_task_sync
from latticeflow.go._generated.api.tasks.update_task import (
    asyncio as update_task_asyncio,
)
from latticeflow.go._generated.api.tasks.update_task import sync as update_task_sync
from latticeflow.go._generated.models.model import Error
from latticeflow.go._generated.models.model import StoredTask
from latticeflow.go._generated.models.model import StoredTasks
from latticeflow.go._generated.models.model import Success
from latticeflow.go._generated.models.model import Task
from latticeflow.go._generated.models.model import TaskTestRequest
from latticeflow.go._generated.models.model import TaskTestResult
from latticeflow.go._generated.types import UNSET
from latticeflow.go._generated.types import Unset
from latticeflow.go.extensions.resources.tasks import (
    AsyncTasksResource as AsyncBaseModule,
)
from latticeflow.go.extensions.resources.tasks import TasksResource as BaseModule
from latticeflow.go.types import ApiError


class TasksResource(BaseModule):
    def delete_task(self, task_id: str, *, delete_evaluations: bool) -> Success:
        """Delete task

        Args:
            task_id (str):
            delete_evaluations (bool):
        """
        with self._base.get_client() as client:
            response = delete_task_sync(
                task_id=task_id, client=client, delete_evaluations=delete_evaluations
            )
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    def test_task(self, task_id: str, body: TaskTestRequest) -> TaskTestResult:
        """Test a task

        Args:
            task_id (str):
            body (TaskTestRequest):
        """
        with self._base.get_client() as client:
            response = test_task_sync(task_id=task_id, body=body, client=client)
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    def get_task(self, task_id: str) -> StoredTask:
        """Get a task

        Args:
            task_id (str):
        """
        with self._base.get_client() as client:
            response = get_task_sync(task_id=task_id, client=client)
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    def update_task(
        self, task_id: str, body: Task, *, invalidate_evaluations: bool
    ) -> StoredTask:
        """Update a task

        Args:
            task_id (str):
            invalidate_evaluations (bool):
            body (Task):
        """
        with self._base.get_client() as client:
            response = update_task_sync(
                task_id=task_id,
                body=body,
                client=client,
                invalidate_evaluations=invalidate_evaluations,
            )
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    def create_task(self, body: Task) -> StoredTask:
        """Create a task

        Args:
            body (Task):
        """
        with self._base.get_client() as client:
            response = create_task_sync(body=body, client=client)
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    def get_tasks(
        self, *, key: Union[Unset, str] = UNSET, user_only: Union[Unset, bool] = False
    ) -> StoredTasks:
        """Get all tasks

        Args:
            key (Union[Unset, str]):
            user_only (Union[Unset, bool]):  Default: False.
        """
        with self._base.get_client() as client:
            response = get_tasks_sync(client=client, key=key, user_only=user_only)
            if isinstance(response, Error):
                raise ApiError(response)
            return response


class AsyncTasksResource(AsyncBaseModule):
    async def delete_task(self, task_id: str, *, delete_evaluations: bool) -> Success:
        """Delete task

        Args:
            task_id (str):
            delete_evaluations (bool):
        """
        with self._base.get_client() as client:
            response = await delete_task_asyncio(
                task_id=task_id, client=client, delete_evaluations=delete_evaluations
            )
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    async def test_task(self, task_id: str, body: TaskTestRequest) -> TaskTestResult:
        """Test a task

        Args:
            task_id (str):
            body (TaskTestRequest):
        """
        with self._base.get_client() as client:
            response = await test_task_asyncio(
                task_id=task_id, body=body, client=client
            )
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    async def get_task(self, task_id: str) -> StoredTask:
        """Get a task

        Args:
            task_id (str):
        """
        with self._base.get_client() as client:
            response = await get_task_asyncio(task_id=task_id, client=client)
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    async def update_task(
        self, task_id: str, body: Task, *, invalidate_evaluations: bool
    ) -> StoredTask:
        """Update a task

        Args:
            task_id (str):
            invalidate_evaluations (bool):
            body (Task):
        """
        with self._base.get_client() as client:
            response = await update_task_asyncio(
                task_id=task_id,
                body=body,
                client=client,
                invalidate_evaluations=invalidate_evaluations,
            )
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    async def create_task(self, body: Task) -> StoredTask:
        """Create a task

        Args:
            body (Task):
        """
        with self._base.get_client() as client:
            response = await create_task_asyncio(body=body, client=client)
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    async def get_tasks(
        self, *, key: Union[Unset, str] = UNSET, user_only: Union[Unset, bool] = False
    ) -> StoredTasks:
        """Get all tasks

        Args:
            key (Union[Unset, str]):
            user_only (Union[Unset, bool]):  Default: False.
        """
        with self._base.get_client() as client:
            response = await get_tasks_asyncio(
                client=client, key=key, user_only=user_only
            )
            if isinstance(response, Error):
                raise ApiError(response)
            return response
