from __future__ import annotations

from latticeflow.go._generated.api.tags.get_tags import asyncio as get_tags_asyncio
from latticeflow.go._generated.api.tags.get_tags import sync as get_tags_sync
from latticeflow.go._generated.models.model import Error
from latticeflow.go._generated.models.model import Tags
from latticeflow.go.base import BaseClient
from latticeflow.go.types import ApiError


class TagsResource:
    def __init__(self, base_client: BaseClient) -> None:
        self._base = base_client

    def get_tags(self) -> Tags:
        """Get all tags currently applied to on any entity."""
        with self._base.get_client() as client:
            response = get_tags_sync(client=client)
            if isinstance(response, Error):
                raise ApiError(response)
            return response


class AsyncTagsResource:
    def __init__(self, base_client: BaseClient) -> None:
        self._base = base_client

    async def get_tags(self) -> Tags:
        """Get all tags currently applied to on any entity."""
        with self._base.get_client() as client:
            response = await get_tags_asyncio(client=client)
            if isinstance(response, Error):
                raise ApiError(response)
            return response
