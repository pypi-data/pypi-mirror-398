from __future__ import annotations

from typing import Union

from latticeflow.go._generated.api.ai_apps.create_ai_app import (
    asyncio as create_ai_app_asyncio,
)
from latticeflow.go._generated.api.ai_apps.create_ai_app import (
    sync as create_ai_app_sync,
)
from latticeflow.go._generated.api.ai_apps.delete_ai_app import (
    asyncio as delete_ai_app_asyncio,
)
from latticeflow.go._generated.api.ai_apps.delete_ai_app import (
    sync as delete_ai_app_sync,
)
from latticeflow.go._generated.api.ai_apps.delete_ai_app_artifact import (
    asyncio as delete_ai_app_artifact_asyncio,
)
from latticeflow.go._generated.api.ai_apps.delete_ai_app_artifact import (
    sync as delete_ai_app_artifact_sync,
)
from latticeflow.go._generated.api.ai_apps.get_ai_app import (
    asyncio as get_ai_app_asyncio,
)
from latticeflow.go._generated.api.ai_apps.get_ai_app import sync as get_ai_app_sync
from latticeflow.go._generated.api.ai_apps.get_ai_app_artifact import (
    asyncio as get_ai_app_artifact_asyncio,
)
from latticeflow.go._generated.api.ai_apps.get_ai_app_artifact import (
    sync as get_ai_app_artifact_sync,
)
from latticeflow.go._generated.api.ai_apps.get_ai_apps import (
    asyncio as get_ai_apps_asyncio,
)
from latticeflow.go._generated.api.ai_apps.get_ai_apps import sync as get_ai_apps_sync
from latticeflow.go._generated.api.ai_apps.update_ai_app import (
    asyncio as update_ai_app_asyncio,
)
from latticeflow.go._generated.api.ai_apps.update_ai_app import (
    sync as update_ai_app_sync,
)
from latticeflow.go._generated.api.ai_apps.upload_ai_app_artifact import (
    asyncio as upload_ai_app_artifact_asyncio,
)
from latticeflow.go._generated.api.ai_apps.upload_ai_app_artifact import (
    sync as upload_ai_app_artifact_sync,
)
from latticeflow.go._generated.models.body import UploadAIAppArtifactBody
from latticeflow.go._generated.models.model import AIApp
from latticeflow.go._generated.models.model import Error
from latticeflow.go._generated.models.model import StoredAIApp
from latticeflow.go._generated.models.model import StoredAIApps
from latticeflow.go._generated.models.model import Success
from latticeflow.go._generated.types import File
from latticeflow.go._generated.types import UNSET
from latticeflow.go._generated.types import Unset
from latticeflow.go.extensions.resources.ai_apps import AiAppsResource as BaseModule
from latticeflow.go.extensions.resources.ai_apps import (
    AsyncAiAppsResource as AsyncBaseModule,
)
from latticeflow.go.types import ApiError


class AiAppsResource(BaseModule):
    def get_ai_app(self, app_id: str) -> StoredAIApp:
        """Get an AI App

        Args:
            app_id (str):
        """
        with self._base.get_client() as client:
            response = get_ai_app_sync(app_id=app_id, client=client)
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    def upload_ai_app_artifact(
        self, app_id: str, body: UploadAIAppArtifactBody
    ) -> Success:
        """Uploads an artifact, associated with an AI app.

        Args:
            app_id (str):
            body (UploadAIAppArtifactBody):
        """
        with self._base.get_client() as client:
            response = upload_ai_app_artifact_sync(
                app_id=app_id, body=body, client=client
            )
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    def delete_ai_app(self, app_id: str) -> Success:
        """Delete an AI app

        Args:
            app_id (str):
        """
        with self._base.get_client() as client:
            response = delete_ai_app_sync(app_id=app_id, client=client)
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    def get_ai_app_artifact(self, app_id: str, artifact_id: str) -> File:
        """Gets an artifact, associated with an AI app.

        Args:
            app_id (str):
            artifact_id (str):
        """
        with self._base.get_client() as client:
            response = get_ai_app_artifact_sync(
                app_id=app_id, artifact_id=artifact_id, client=client
            )
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    def create_ai_app(self, body: AIApp) -> StoredAIApp:
        """Create an AI App

        Args:
            body (AIApp): An AI app represents a workspace to execute technical assessments of the AI
                use case.
        """
        with self._base.get_client() as client:
            response = create_ai_app_sync(body=body, client=client)
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    def delete_ai_app_artifact(self, app_id: str, artifact_id: str) -> Success:
        """Deletes an artifact, associated with an AI app.

        Args:
            app_id (str):
            artifact_id (str):
        """
        with self._base.get_client() as client:
            response = delete_ai_app_artifact_sync(
                app_id=app_id, artifact_id=artifact_id, client=client
            )
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    def get_ai_apps(self, *, key: Union[Unset, str] = UNSET) -> StoredAIApps:
        """Get all AI Apps

        Args:
            key (Union[Unset, str]):
        """
        with self._base.get_client() as client:
            response = get_ai_apps_sync(client=client, key=key)
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    def update_ai_app(self, app_id: str, body: AIApp) -> StoredAIApp:
        """Update an AI app

        Args:
            app_id (str):
            body (AIApp): An AI app represents a workspace to execute technical assessments of the AI
                use case.
        """
        with self._base.get_client() as client:
            response = update_ai_app_sync(app_id=app_id, body=body, client=client)
            if isinstance(response, Error):
                raise ApiError(response)
            return response


class AsyncAiAppsResource(AsyncBaseModule):
    async def get_ai_app(self, app_id: str) -> StoredAIApp:
        """Get an AI App

        Args:
            app_id (str):
        """
        with self._base.get_client() as client:
            response = await get_ai_app_asyncio(app_id=app_id, client=client)
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    async def upload_ai_app_artifact(
        self, app_id: str, body: UploadAIAppArtifactBody
    ) -> Success:
        """Uploads an artifact, associated with an AI app.

        Args:
            app_id (str):
            body (UploadAIAppArtifactBody):
        """
        with self._base.get_client() as client:
            response = await upload_ai_app_artifact_asyncio(
                app_id=app_id, body=body, client=client
            )
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    async def delete_ai_app(self, app_id: str) -> Success:
        """Delete an AI app

        Args:
            app_id (str):
        """
        with self._base.get_client() as client:
            response = await delete_ai_app_asyncio(app_id=app_id, client=client)
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    async def get_ai_app_artifact(self, app_id: str, artifact_id: str) -> File:
        """Gets an artifact, associated with an AI app.

        Args:
            app_id (str):
            artifact_id (str):
        """
        with self._base.get_client() as client:
            response = await get_ai_app_artifact_asyncio(
                app_id=app_id, artifact_id=artifact_id, client=client
            )
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    async def create_ai_app(self, body: AIApp) -> StoredAIApp:
        """Create an AI App

        Args:
            body (AIApp): An AI app represents a workspace to execute technical assessments of the AI
                use case.
        """
        with self._base.get_client() as client:
            response = await create_ai_app_asyncio(body=body, client=client)
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    async def delete_ai_app_artifact(self, app_id: str, artifact_id: str) -> Success:
        """Deletes an artifact, associated with an AI app.

        Args:
            app_id (str):
            artifact_id (str):
        """
        with self._base.get_client() as client:
            response = await delete_ai_app_artifact_asyncio(
                app_id=app_id, artifact_id=artifact_id, client=client
            )
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    async def get_ai_apps(self, *, key: Union[Unset, str] = UNSET) -> StoredAIApps:
        """Get all AI Apps

        Args:
            key (Union[Unset, str]):
        """
        with self._base.get_client() as client:
            response = await get_ai_apps_asyncio(client=client, key=key)
            if isinstance(response, Error):
                raise ApiError(response)
            return response

    async def update_ai_app(self, app_id: str, body: AIApp) -> StoredAIApp:
        """Update an AI app

        Args:
            app_id (str):
            body (AIApp): An AI app represents a workspace to execute technical assessments of the AI
                use case.
        """
        with self._base.get_client() as client:
            response = await update_ai_app_asyncio(
                app_id=app_id, body=body, client=client
            )
            if isinstance(response, Error):
                raise ApiError(response)
            return response
