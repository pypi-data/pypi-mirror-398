from __future__ import annotations

import httpx


SDK_PACKAGE_NAME = "latticeflow-go-sdk"
DEFAULT_PLACEHOLDER_VERSION = "0.0.0.dev0"
API_KEY_HEADER = "X-LatticeFlow-API-Key"
CLIENT_VERSION_HEADER = "X-LatticeFlow-Client-Version"
DEFAULT_HTTP_TIMEOUT = httpx.Timeout(connect=3.0, read=10.0, write=10.0, pool=3.0)
