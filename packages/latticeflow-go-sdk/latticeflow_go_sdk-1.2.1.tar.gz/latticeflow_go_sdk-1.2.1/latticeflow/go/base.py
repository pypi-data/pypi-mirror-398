from __future__ import annotations

import httpx

from latticeflow.go._generated.client import Client as _Client
from latticeflow.go.utils.constants import API_KEY_HEADER
from latticeflow.go.utils.constants import CLIENT_VERSION_HEADER
from latticeflow.go.utils.sdk_version import get_sdk_version


class BaseClient:
    def __init__(
        self,
        base_url: str,
        api_key: str | None,
        *,
        verify_ssl: bool,
        timeout: httpx.Timeout,
    ) -> None:
        """Base API Client.

        Args:
            base_url: The base URL for the API, all requests are made to a relative path to this URL
            api_key: The API key to use for authentication (`None` if no authentication)
            verify_ssl: Whether to verify the SSL certificate of the API server. This should be True in production, but can be set to False for testing purposes.
            timeout: The timeout to be used for HTTP requests.
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.verify_ssl = verify_ssl
        self.timeout = timeout

    def get_client(self) -> _Client:
        headers = {}
        if sdk_version := get_sdk_version():
            headers[CLIENT_VERSION_HEADER] = f"sdk@{sdk_version}"
        if self.api_key:
            headers[API_KEY_HEADER] = self.api_key

        return _Client(
            base_url=f"{self.base_url}/api",
            headers=headers,
            verify_ssl=self.verify_ssl,
            timeout=self.timeout,
        )
