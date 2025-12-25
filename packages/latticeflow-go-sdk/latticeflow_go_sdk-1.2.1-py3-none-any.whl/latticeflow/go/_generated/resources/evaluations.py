from __future__ import annotations

from latticeflow.go._generated.api.evaluations.create_evaluation import (
    asyncio as create_evaluation_asyncio,
)
from latticeflow.go._generated.api.evaluations.create_evaluation import (
    sync as create_evaluation_sync,
)
from latticeflow.go._generated.api.evaluations.download_evaluation_result import (
    asyncio as download_evaluation_result_asyncio,
)
from latticeflow.go._generated.api.evaluations.download_evaluation_result import (
    sync as download_evaluation_result_sync,
)
from latticeflow.go._generated.api.evaluations.execute_action_evaluation import (
    asyncio as execute_action_evaluation_asyncio,
)
from latticeflow.go._generated.api.evaluations.execute_action_evaluation import (
    sync as execute_action_evaluation_sync,
)
from latticeflow.go._generated.api.evaluations.get_evaluation import (
    asyncio as get_evaluation_asyncio,
)
from latticeflow.go._generated.api.evaluations.get_evaluation import (
    sync as get_evaluation_sync,
)
from latticeflow.go._generated.api.evaluations.get_evaluations import (
    asyncio as get_evaluations_asyncio,
)
from latticeflow.go._generated.api.evaluations.get_evaluations import (
    sync as get_evaluations_sync,
)
from latticeflow.go._generated.models.model import Error
from latticeflow.go._generated.models.model import Evaluation
from latticeflow.go._generated.models.model import EvaluationAction
from latticeflow.go._generated.models.model import StoredEvaluation
from latticeflow.go._generated.models.model import StoredEvaluations
from latticeflow.go._generated.models.model import Success
from latticeflow.go._generated.types import File
from latticeflow.go.base import BaseClient
from latticeflow.go.types import ApiError


class EvaluationsResource:
    def __init__(self, base_client: BaseClient) -> None:
        self._base = base_client

    def download_evaluation_result(self, app_id: str, evaluation_id: str) -> File:
        """Download evaluation result (as a ZIP file).

        Args:
            app_id (str):
            evaluation_id (str):
        """
        with self._base.get_client() as client:
            response = download_evaluation_result_sync(
                app_id=app_id, evaluation_id=evaluation_id, client=client
            )
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    def create_evaluation(self, app_id: str, body: Evaluation) -> StoredEvaluation:
        """Create a new evaluation

        Args:
            app_id (str):
            body (Evaluation): This entity tracks the execution of multiple tasks.
        """
        with self._base.get_client() as client:
            response = create_evaluation_sync(app_id=app_id, body=body, client=client)
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    def get_evaluations(self, app_id: str) -> StoredEvaluations:
        """Get all evaluations.

        Args:
            app_id (str):
        """
        with self._base.get_client() as client:
            response = get_evaluations_sync(app_id=app_id, client=client)
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    def get_evaluation(self, app_id: str, evaluation_id: str) -> StoredEvaluation:
        """Gets an evaluation.

        Args:
            app_id (str):
            evaluation_id (str):
        """
        with self._base.get_client() as client:
            response = get_evaluation_sync(
                app_id=app_id, evaluation_id=evaluation_id, client=client
            )
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    def execute_action_evaluation(
        self, app_id: str, evaluation_id: str, *, action: EvaluationAction
    ) -> Success:
        """Execute an action on an evaluation.

        Args:
            app_id (str):
            evaluation_id (str):
            action (EvaluationAction): The action to perform on the given evaluation.

                The available actions and their meanings are:
                - start - Starts the given evaluation. If already running or finished, it will be rerun
                and all existing tasks terminated.
                - cancel - Stops and invalidates all running tasks in the evaluation. Fails if no tasks
                are running.
        """
        with self._base.get_client() as client:
            response = execute_action_evaluation_sync(
                app_id=app_id, evaluation_id=evaluation_id, client=client, action=action
            )
            if isinstance(response, Error):
                raise ApiError(response)
            return response


class AsyncEvaluationsResource:
    def __init__(self, base_client: BaseClient) -> None:
        self._base = base_client

    async def download_evaluation_result(self, app_id: str, evaluation_id: str) -> File:
        """Download evaluation result (as a ZIP file).

        Args:
            app_id (str):
            evaluation_id (str):
        """
        with self._base.get_client() as client:
            response = await download_evaluation_result_asyncio(
                app_id=app_id, evaluation_id=evaluation_id, client=client
            )
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    async def create_evaluation(
        self, app_id: str, body: Evaluation
    ) -> StoredEvaluation:
        """Create a new evaluation

        Args:
            app_id (str):
            body (Evaluation): This entity tracks the execution of multiple tasks.
        """
        with self._base.get_client() as client:
            response = await create_evaluation_asyncio(
                app_id=app_id, body=body, client=client
            )
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    async def get_evaluations(self, app_id: str) -> StoredEvaluations:
        """Get all evaluations.

        Args:
            app_id (str):
        """
        with self._base.get_client() as client:
            response = await get_evaluations_asyncio(app_id=app_id, client=client)
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    async def get_evaluation(self, app_id: str, evaluation_id: str) -> StoredEvaluation:
        """Gets an evaluation.

        Args:
            app_id (str):
            evaluation_id (str):
        """
        with self._base.get_client() as client:
            response = await get_evaluation_asyncio(
                app_id=app_id, evaluation_id=evaluation_id, client=client
            )
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    async def execute_action_evaluation(
        self, app_id: str, evaluation_id: str, *, action: EvaluationAction
    ) -> Success:
        """Execute an action on an evaluation.

        Args:
            app_id (str):
            evaluation_id (str):
            action (EvaluationAction): The action to perform on the given evaluation.

                The available actions and their meanings are:
                - start - Starts the given evaluation. If already running or finished, it will be rerun
                and all existing tasks terminated.
                - cancel - Stops and invalidates all running tasks in the evaluation. Fails if no tasks
                are running.
        """
        with self._base.get_client() as client:
            response = await execute_action_evaluation_asyncio(
                app_id=app_id, evaluation_id=evaluation_id, client=client, action=action
            )
            if isinstance(response, Error):
                raise ApiError(response)
            return response
