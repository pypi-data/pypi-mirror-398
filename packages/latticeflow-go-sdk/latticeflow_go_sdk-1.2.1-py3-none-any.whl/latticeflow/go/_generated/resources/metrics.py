from __future__ import annotations

from latticeflow.go._generated.api.metrics.get_metrics import (
    asyncio as get_metrics_asyncio,
)
from latticeflow.go._generated.api.metrics.get_metrics import sync as get_metrics_sync
from latticeflow.go._generated.models.model import Error
from latticeflow.go._generated.models.model import StoredMetrics
from latticeflow.go.base import BaseClient
from latticeflow.go.types import ApiError


class MetricsResource:
    def __init__(self, base_client: BaseClient) -> None:
        self._base = base_client

    def get_metrics(self) -> StoredMetrics:
        """Get all metrics."""
        with self._base.get_client() as client:
            response = get_metrics_sync(client=client)
            if isinstance(response, Error):
                raise ApiError(response)
            return response


class AsyncMetricsResource:
    def __init__(self, base_client: BaseClient) -> None:
        self._base = base_client

    async def get_metrics(self) -> StoredMetrics:
        """Get all metrics."""
        with self._base.get_client() as client:
            response = await get_metrics_asyncio(client=client)
            if isinstance(response, Error):
                raise ApiError(response)
            return response
