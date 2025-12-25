from __future__ import annotations

import json
import os
from pathlib import Path

import latticeflow.go.cli.utils.exceptions as cli_exc
from latticeflow.go.cli.utils.constants import LF_AIGO_URL_NAME
from latticeflow.go.cli.utils.constants import LF_API_KEY_NAME
from latticeflow.go.cli.utils.constants import LF_API_TIMEOUT_NAME
from latticeflow.go.cli.utils.constants import LF_OWNER_KEY_NAME
from latticeflow.go.cli.utils.constants import LF_VERIFY_SSL_NAME
from latticeflow.go.cli.utils.dtypes import EnvVars


def _parse_timeout_env_var(timeout_str: str | None) -> float | None:
    if not timeout_str:
        return None
    try:
        return float(timeout_str)
    except ValueError:
        raise cli_exc.CLIConfigurationError(
            f"The AI GO! `{LF_API_TIMEOUT_NAME}` value must be a number "
            f"representing the timeout in seconds, but got '{timeout_str}'."
        )


def get_cli_env_vars() -> EnvVars:
    aigo_url = os.getenv(LF_AIGO_URL_NAME)
    api_key = os.getenv(LF_API_KEY_NAME)
    verify_ssl = os.getenv(LF_VERIFY_SSL_NAME, "True") == "True"
    timeout = _parse_timeout_env_var(os.getenv(LF_API_TIMEOUT_NAME))

    if aigo_url and api_key:
        return EnvVars(
            base_url=aigo_url, api_key=api_key, verify_ssl=verify_ssl, timeout=timeout
        )

    aigo_url, api_key, verify_ssl = _get_env_vars_from_config_file()

    if aigo_url is None:
        raise cli_exc.CLIConfigurationError(
            f"The AI GO! `{LF_AIGO_URL_NAME}` value is missing. "
            f"You can set it via the `{LF_AIGO_URL_NAME}` environment "
            "variable or using the `lf configure` command."
        )
    if api_key is None:
        raise cli_exc.CLIConfigurationError(
            f"The AI GO! `{LF_API_KEY_NAME}` value is missing. "
            f"You can set it via the `{LF_API_KEY_NAME}` environment "
            "variable or using the `lf configure` command."
        )

    return EnvVars(
        base_url=aigo_url, api_key=api_key, verify_ssl=verify_ssl, timeout=timeout
    )


def get_tenant_cli_env_vars() -> EnvVars:
    aigo_url = os.getenv(LF_AIGO_URL_NAME)
    timeout = _parse_timeout_env_var(os.getenv(LF_API_TIMEOUT_NAME))
    # If we do not have owner key, we raise immediately, because
    # it cannot be configured using `lf configure`
    if not (owner_key := os.getenv(LF_OWNER_KEY_NAME)):
        raise cli_exc.CLIConfigurationError(
            f"The AI GO! `{LF_OWNER_KEY_NAME}` value is missing."
        )
    verify_ssl = os.getenv(LF_VERIFY_SSL_NAME, "True") == "True"

    if aigo_url:
        return EnvVars(
            base_url=aigo_url, api_key=owner_key, verify_ssl=verify_ssl, timeout=timeout
        )

    aigo_url, _, verify_ssl = _get_env_vars_from_config_file()

    if aigo_url is None:
        raise cli_exc.CLIConfigurationError(
            f"The AI GO! `{LF_AIGO_URL_NAME}` value is missing. "
            f"You can set it via the `{LF_AIGO_URL_NAME}` environment "
            "variable or using the `lf configure` command."
        )

    return EnvVars(
        base_url=aigo_url, api_key=owner_key, verify_ssl=verify_ssl, timeout=timeout
    )


def get_init_setup_cli_env_vars() -> str:
    if aigo_url := os.getenv(LF_AIGO_URL_NAME):
        return aigo_url

    aigo_url, _, _ = _get_env_vars_from_config_file()

    if aigo_url is None:
        raise cli_exc.CLIConfigurationError(
            f"The AI GO! `{LF_AIGO_URL_NAME}` value is missing. "
            f"You can set it via the `{LF_AIGO_URL_NAME}` environment "
            "variable or using the `lf configure` command."
        )

    return aigo_url


def _get_env_vars_from_config_file() -> tuple[str | None, str | None, bool]:
    config_file = Path.home() / ".latticeflow" / "config.json"

    if not config_file.exists():
        raise cli_exc.CLIConfigurationError(
            f"Config file not found at {config_file}. "
            "Please configure the CLI using the `lf configure` command."
        )

    with open(config_file, "r") as f:
        config = json.load(f)

    aigo_url = config.get(LF_AIGO_URL_NAME)
    api_key = config.get(LF_API_KEY_NAME)
    verify_ssl = config.get(LF_VERIFY_SSL_NAME, True)

    if aigo_url is not None and not isinstance(aigo_url, str):
        raise cli_exc.CLIConfigurationError(
            f"The AI GO! `{LF_AIGO_URL_NAME}` value saved in the configuration file "
            f"must be a string, but was of type '{type(aigo_url).__name__}' "
            f"with value '{aigo_url}'."
        )
    if api_key is not None and not isinstance(api_key, str):
        raise cli_exc.CLIConfigurationError(
            f"The AI GO! `{LF_API_KEY_NAME}` value saved in the configuration file "
            f"must be a string, but was of type '{type(api_key).__name__}' "
            f"with value '{api_key}'."
        )
    if not isinstance(verify_ssl, bool):
        raise cli_exc.CLIConfigurationError(
            f"The AI GO! `{LF_VERIFY_SSL_NAME}` value saved in the configuration file "
            f"must be a boolean, but was of type '{type(verify_ssl).__name__}' "
            f"with value '{verify_ssl}'."
        )

    return aigo_url, api_key, verify_ssl
