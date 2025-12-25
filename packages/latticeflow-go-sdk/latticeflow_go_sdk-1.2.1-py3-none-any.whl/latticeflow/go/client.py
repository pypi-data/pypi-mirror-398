from __future__ import annotations

import httpx

from latticeflow.go._generated.resources.ai_apps import AiAppsResource
from latticeflow.go._generated.resources.ai_apps import AsyncAiAppsResource
from latticeflow.go._generated.resources.dataset_generators import (
    AsyncDatasetGeneratorsResource,
)
from latticeflow.go._generated.resources.dataset_generators import (
    DatasetGeneratorsResource,
)
from latticeflow.go._generated.resources.datasets import AsyncDatasetsResource
from latticeflow.go._generated.resources.datasets import DatasetsResource
from latticeflow.go._generated.resources.evaluations import AsyncEvaluationsResource
from latticeflow.go._generated.resources.evaluations import EvaluationsResource
from latticeflow.go._generated.resources.integrations import AsyncIntegrationsResource
from latticeflow.go._generated.resources.integrations import IntegrationsResource
from latticeflow.go._generated.resources.metrics import AsyncMetricsResource
from latticeflow.go._generated.resources.metrics import MetricsResource
from latticeflow.go._generated.resources.model_adapters import (
    AsyncModelAdaptersResource,
)
from latticeflow.go._generated.resources.model_adapters import ModelAdaptersResource
from latticeflow.go._generated.resources.models import AsyncModelsResource
from latticeflow.go._generated.resources.models import ModelsResource
from latticeflow.go._generated.resources.scorers import AsyncScorersResource
from latticeflow.go._generated.resources.scorers import ScorersResource
from latticeflow.go._generated.resources.setup import AsyncSetupResource
from latticeflow.go._generated.resources.setup import SetupResource
from latticeflow.go._generated.resources.tags import AsyncTagsResource
from latticeflow.go._generated.resources.tags import TagsResource
from latticeflow.go._generated.resources.task_results import AsyncTaskResultsResource
from latticeflow.go._generated.resources.task_results import TaskResultsResource
from latticeflow.go._generated.resources.tasks import AsyncTasksResource
from latticeflow.go._generated.resources.tasks import TasksResource
from latticeflow.go._generated.resources.tenants import AsyncTenantsResource
from latticeflow.go._generated.resources.tenants import TenantsResource
from latticeflow.go._generated.resources.users import AsyncUsersResource
from latticeflow.go._generated.resources.users import UsersResource
from latticeflow.go.base import BaseClient
from latticeflow.go.utils.constants import DEFAULT_HTTP_TIMEOUT


class Client(BaseClient):
    def __init__(
        self,
        base_url: str,
        api_key: str | None,
        *,
        verify_ssl: bool = True,
        timeout: httpx.Timeout = DEFAULT_HTTP_TIMEOUT,
    ) -> None:
        """Synchronous API Client.

        Args:
            base_url: The base URL for the API, all requests are made to a relative path to this URL
            api_key: The API key to use for authentication (`None` if no authentication)
            verify_ssl: Whether to verify the SSL certificate of the API server. This should be True in production, but can be set to False for testing purposes.
            timeout: The timeout to be used for HTTP requests.
        """
        super().__init__(
            base_url=base_url, api_key=api_key, verify_ssl=verify_ssl, timeout=timeout
        )

    @property
    def tags(self) -> TagsResource:
        return TagsResource(self)

    @property
    def dataset_generators(self) -> DatasetGeneratorsResource:
        return DatasetGeneratorsResource(self)

    @property
    def task_results(self) -> TaskResultsResource:
        return TaskResultsResource(self)

    @property
    def model_adapters(self) -> ModelAdaptersResource:
        return ModelAdaptersResource(self)

    @property
    def scorers(self) -> ScorersResource:
        return ScorersResource(self)

    @property
    def tenants(self) -> TenantsResource:
        return TenantsResource(self)

    @property
    def users(self) -> UsersResource:
        return UsersResource(self)

    @property
    def setup(self) -> SetupResource:
        return SetupResource(self)

    @property
    def metrics(self) -> MetricsResource:
        return MetricsResource(self)

    @property
    def evaluations(self) -> EvaluationsResource:
        return EvaluationsResource(self)

    @property
    def models(self) -> ModelsResource:
        return ModelsResource(self)

    @property
    def tasks(self) -> TasksResource:
        return TasksResource(self)

    @property
    def datasets(self) -> DatasetsResource:
        return DatasetsResource(self)

    @property
    def ai_apps(self) -> AiAppsResource:
        return AiAppsResource(self)

    @property
    def integrations(self) -> IntegrationsResource:
        return IntegrationsResource(self)


class AsyncClient(BaseClient):
    def __init__(
        self,
        base_url: str,
        api_key: str | None,
        *,
        verify_ssl: bool = True,
        timeout: httpx.Timeout = DEFAULT_HTTP_TIMEOUT,
    ) -> None:
        """Asynchronous API Client.

        Args:
            base_url: The base URL for the API, all requests are made to a relative path to this URL
            api_key: The API key to use for authentication (`None` if no authentication)
            verify_ssl: Whether to verify the SSL certificate of the API server. This should be True in production, but can be set to False for testing purposes.
            timeout: The timeout to be used for HTTP requests.
        """
        super().__init__(
            base_url=base_url, api_key=api_key, verify_ssl=verify_ssl, timeout=timeout
        )

    @property
    def tags(self) -> AsyncTagsResource:
        return AsyncTagsResource(self)

    @property
    def dataset_generators(self) -> AsyncDatasetGeneratorsResource:
        return AsyncDatasetGeneratorsResource(self)

    @property
    def task_results(self) -> AsyncTaskResultsResource:
        return AsyncTaskResultsResource(self)

    @property
    def model_adapters(self) -> AsyncModelAdaptersResource:
        return AsyncModelAdaptersResource(self)

    @property
    def scorers(self) -> AsyncScorersResource:
        return AsyncScorersResource(self)

    @property
    def tenants(self) -> AsyncTenantsResource:
        return AsyncTenantsResource(self)

    @property
    def users(self) -> AsyncUsersResource:
        return AsyncUsersResource(self)

    @property
    def setup(self) -> AsyncSetupResource:
        return AsyncSetupResource(self)

    @property
    def metrics(self) -> AsyncMetricsResource:
        return AsyncMetricsResource(self)

    @property
    def evaluations(self) -> AsyncEvaluationsResource:
        return AsyncEvaluationsResource(self)

    @property
    def models(self) -> AsyncModelsResource:
        return AsyncModelsResource(self)

    @property
    def tasks(self) -> AsyncTasksResource:
        return AsyncTasksResource(self)

    @property
    def datasets(self) -> AsyncDatasetsResource:
        return AsyncDatasetsResource(self)

    @property
    def ai_apps(self) -> AsyncAiAppsResource:
        return AsyncAiAppsResource(self)

    @property
    def integrations(self) -> AsyncIntegrationsResource:
        return AsyncIntegrationsResource(self)
