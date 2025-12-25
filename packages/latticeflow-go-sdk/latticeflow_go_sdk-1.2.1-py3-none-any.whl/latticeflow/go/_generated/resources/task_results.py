from __future__ import annotations

from latticeflow.go._generated.api.task_results.cancel_task_result import (
    asyncio as cancel_task_result_asyncio,
)
from latticeflow.go._generated.api.task_results.cancel_task_result import (
    sync as cancel_task_result_sync,
)
from latticeflow.go._generated.api.task_results.create_task_result import (
    asyncio as create_task_result_asyncio,
)
from latticeflow.go._generated.api.task_results.create_task_result import (
    sync as create_task_result_sync,
)
from latticeflow.go._generated.api.task_results.create_task_result_report import (
    asyncio as create_task_result_report_asyncio,
)
from latticeflow.go._generated.api.task_results.create_task_result_report import (
    sync as create_task_result_report_sync,
)
from latticeflow.go._generated.api.task_results.delete_task_result import (
    asyncio as delete_task_result_asyncio,
)
from latticeflow.go._generated.api.task_results.delete_task_result import (
    sync as delete_task_result_sync,
)
from latticeflow.go._generated.api.task_results.download_task_result_log import (
    asyncio as download_task_result_log_asyncio,
)
from latticeflow.go._generated.api.task_results.download_task_result_log import (
    sync as download_task_result_log_sync,
)
from latticeflow.go._generated.api.task_results.get_task_result import (
    asyncio as get_task_result_asyncio,
)
from latticeflow.go._generated.api.task_results.get_task_result import (
    sync as get_task_result_sync,
)
from latticeflow.go._generated.api.task_results.get_task_result_evidence import (
    asyncio as get_task_result_evidence_asyncio,
)
from latticeflow.go._generated.api.task_results.get_task_result_evidence import (
    sync as get_task_result_evidence_sync,
)
from latticeflow.go._generated.api.task_results.get_task_result_report import (
    asyncio as get_task_result_report_asyncio,
)
from latticeflow.go._generated.api.task_results.get_task_result_report import (
    sync as get_task_result_report_sync,
)
from latticeflow.go._generated.api.task_results.invalidate_task_result_cache import (
    asyncio as invalidate_task_result_cache_asyncio,
)
from latticeflow.go._generated.api.task_results.invalidate_task_result_cache import (
    sync as invalidate_task_result_cache_sync,
)
from latticeflow.go._generated.api.task_results.run_task_result import (
    asyncio as run_task_result_asyncio,
)
from latticeflow.go._generated.api.task_results.run_task_result import (
    sync as run_task_result_sync,
)
from latticeflow.go._generated.api.task_results.update_task_result import (
    asyncio as update_task_result_asyncio,
)
from latticeflow.go._generated.api.task_results.update_task_result import (
    sync as update_task_result_sync,
)
from latticeflow.go._generated.models.body import CreateTaskResultBody
from latticeflow.go._generated.models.model import Error
from latticeflow.go._generated.models.model import Report
from latticeflow.go._generated.models.model import StoredTaskResult
from latticeflow.go._generated.models.model import Success
from latticeflow.go._generated.models.model import TaskResult
from latticeflow.go._generated.models.model import TaskResultEvidence
from latticeflow.go._generated.types import File
from latticeflow.go.base import BaseClient
from latticeflow.go.types import ApiError


class TaskResultsResource:
    def __init__(self, base_client: BaseClient) -> None:
        self._base = base_client

    def get_task_result(self, task_result_id: str) -> StoredTaskResult:
        """Get a task result

        Args:
            task_result_id (str):
        """
        with self._base.get_client() as client:
            response = get_task_result_sync(
                task_result_id=task_result_id, client=client
            )
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    def create_task_result_report(self, task_result_id: str) -> Report:
        """Creates a new report for task result.

        Args:
            task_result_id (str):
        """
        with self._base.get_client() as client:
            response = create_task_result_report_sync(
                task_result_id=task_result_id, client=client
            )
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    def cancel_task_result(self, task_result_id: str) -> Success:
        """Cancel a task result

        Args:
            task_result_id (str):
        """
        with self._base.get_client() as client:
            response = cancel_task_result_sync(
                task_result_id=task_result_id, client=client
            )
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    def get_task_result_evidence(self, task_result_id: str) -> TaskResultEvidence:
        """Get the task result evidence by ID in JSON format.

        Args:
            task_result_id (str):
        """
        with self._base.get_client() as client:
            response = get_task_result_evidence_sync(
                task_result_id=task_result_id, client=client
            )
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    def create_task_result(self, body: CreateTaskResultBody) -> StoredTaskResult:
        """Create a task result

        Args:
            body (CreateTaskResultBody):
        """
        with self._base.get_client() as client:
            response = create_task_result_sync(body=body, client=client)
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    def run_task_result(self, task_result_id: str) -> Success:
        """Schedule a task result run

        Args:
            task_result_id (str):
        """
        with self._base.get_client() as client:
            response = run_task_result_sync(
                task_result_id=task_result_id, client=client
            )
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    def invalidate_task_result_cache(self, task_result_id: str) -> Report:
        """Invalidates the cache for a task result.

        Args:
            task_result_id (str):
        """
        with self._base.get_client() as client:
            response = invalidate_task_result_cache_sync(
                task_result_id=task_result_id, client=client
            )
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    def delete_task_result(self, task_result_id: str) -> Success:
        """Delete a task result

        Args:
            task_result_id (str):
        """
        with self._base.get_client() as client:
            response = delete_task_result_sync(
                task_result_id=task_result_id, client=client
            )
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    def download_task_result_log(self, task_result_id: str) -> File:
        """Download a task result's log.

        Args:
            task_result_id (str):
        """
        with self._base.get_client() as client:
            response = download_task_result_log_sync(
                task_result_id=task_result_id, client=client
            )
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    def update_task_result(
        self, task_result_id: str, body: TaskResult
    ) -> StoredTaskResult:
        """Update a task result.

        Args:
            task_result_id (str):
            body (TaskResult):
        """
        with self._base.get_client() as client:
            response = update_task_result_sync(
                task_result_id=task_result_id, body=body, client=client
            )
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    def get_task_result_report(self, task_result_id: str) -> Report:
        """Retrieves the report, associated to a task result.

        Args:
            task_result_id (str):
        """
        with self._base.get_client() as client:
            response = get_task_result_report_sync(
                task_result_id=task_result_id, client=client
            )
            if isinstance(response, Error):
                raise ApiError(response)
            return response


class AsyncTaskResultsResource:
    def __init__(self, base_client: BaseClient) -> None:
        self._base = base_client

    async def get_task_result(self, task_result_id: str) -> StoredTaskResult:
        """Get a task result

        Args:
            task_result_id (str):
        """
        with self._base.get_client() as client:
            response = await get_task_result_asyncio(
                task_result_id=task_result_id, client=client
            )
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    async def create_task_result_report(self, task_result_id: str) -> Report:
        """Creates a new report for task result.

        Args:
            task_result_id (str):
        """
        with self._base.get_client() as client:
            response = await create_task_result_report_asyncio(
                task_result_id=task_result_id, client=client
            )
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    async def cancel_task_result(self, task_result_id: str) -> Success:
        """Cancel a task result

        Args:
            task_result_id (str):
        """
        with self._base.get_client() as client:
            response = await cancel_task_result_asyncio(
                task_result_id=task_result_id, client=client
            )
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    async def get_task_result_evidence(self, task_result_id: str) -> TaskResultEvidence:
        """Get the task result evidence by ID in JSON format.

        Args:
            task_result_id (str):
        """
        with self._base.get_client() as client:
            response = await get_task_result_evidence_asyncio(
                task_result_id=task_result_id, client=client
            )
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    async def create_task_result(self, body: CreateTaskResultBody) -> StoredTaskResult:
        """Create a task result

        Args:
            body (CreateTaskResultBody):
        """
        with self._base.get_client() as client:
            response = await create_task_result_asyncio(body=body, client=client)
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    async def run_task_result(self, task_result_id: str) -> Success:
        """Schedule a task result run

        Args:
            task_result_id (str):
        """
        with self._base.get_client() as client:
            response = await run_task_result_asyncio(
                task_result_id=task_result_id, client=client
            )
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    async def invalidate_task_result_cache(self, task_result_id: str) -> Report:
        """Invalidates the cache for a task result.

        Args:
            task_result_id (str):
        """
        with self._base.get_client() as client:
            response = await invalidate_task_result_cache_asyncio(
                task_result_id=task_result_id, client=client
            )
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    async def delete_task_result(self, task_result_id: str) -> Success:
        """Delete a task result

        Args:
            task_result_id (str):
        """
        with self._base.get_client() as client:
            response = await delete_task_result_asyncio(
                task_result_id=task_result_id, client=client
            )
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    async def download_task_result_log(self, task_result_id: str) -> File:
        """Download a task result's log.

        Args:
            task_result_id (str):
        """
        with self._base.get_client() as client:
            response = await download_task_result_log_asyncio(
                task_result_id=task_result_id, client=client
            )
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    async def update_task_result(
        self, task_result_id: str, body: TaskResult
    ) -> StoredTaskResult:
        """Update a task result.

        Args:
            task_result_id (str):
            body (TaskResult):
        """
        with self._base.get_client() as client:
            response = await update_task_result_asyncio(
                task_result_id=task_result_id, body=body, client=client
            )
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    async def get_task_result_report(self, task_result_id: str) -> Report:
        """Retrieves the report, associated to a task result.

        Args:
            task_result_id (str):
        """
        with self._base.get_client() as client:
            response = await get_task_result_report_asyncio(
                task_result_id=task_result_id, client=client
            )
            if isinstance(response, Error):
                raise ApiError(response)
            return response
