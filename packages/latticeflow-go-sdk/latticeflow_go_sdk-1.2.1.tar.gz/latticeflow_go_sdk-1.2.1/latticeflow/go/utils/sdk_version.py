from __future__ import annotations

from importlib.metadata import version

from latticeflow.go.utils.constants import DEFAULT_PLACEHOLDER_VERSION
from latticeflow.go.utils.constants import SDK_PACKAGE_NAME


def get_sdk_version() -> str | None:
    semver = version(SDK_PACKAGE_NAME)
    return None if semver == DEFAULT_PLACEHOLDER_VERSION else semver
