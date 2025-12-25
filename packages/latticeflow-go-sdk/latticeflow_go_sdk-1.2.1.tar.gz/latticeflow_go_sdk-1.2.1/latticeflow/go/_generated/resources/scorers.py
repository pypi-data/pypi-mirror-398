from __future__ import annotations

from latticeflow.go._generated.api.scorers.get_scorers import (
    asyncio as get_scorers_asyncio,
)
from latticeflow.go._generated.api.scorers.get_scorers import sync as get_scorers_sync
from latticeflow.go._generated.models.model import Error
from latticeflow.go._generated.models.model import StoredScorers
from latticeflow.go.base import BaseClient
from latticeflow.go.types import ApiError


class ScorersResource:
    def __init__(self, base_client: BaseClient) -> None:
        self._base = base_client

    def get_scorers(self) -> StoredScorers:
        """Get all scorers."""
        with self._base.get_client() as client:
            response = get_scorers_sync(client=client)
            if isinstance(response, Error):
                raise ApiError(response)
            return response


class AsyncScorersResource:
    def __init__(self, base_client: BaseClient) -> None:
        self._base = base_client

    async def get_scorers(self) -> StoredScorers:
        """Get all scorers."""
        with self._base.get_client() as client:
            response = await get_scorers_asyncio(client=client)
            if isinstance(response, Error):
                raise ApiError(response)
            return response
