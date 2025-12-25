from __future__ import annotations

import typer

import latticeflow.go.cli.utils.printing as cli_print
from latticeflow.go import Client
from latticeflow.go.cli.utils.configuration import get_configuration_file
from latticeflow.go.cli.utils.configuration import upsert_configuration_file
from latticeflow.go.cli.utils.constants import LF_AIGO_URL_NAME
from latticeflow.go.cli.utils.constants import LF_API_KEY_NAME
from latticeflow.go.cli.utils.constants import LF_APP_KEY_CONTEXT_NAME
from latticeflow.go.cli.utils.constants import LF_VERIFY_SSL_NAME
from latticeflow.go.cli.utils.env_vars import get_cli_env_vars
from latticeflow.go.cli.utils.exceptions import CLIError
from latticeflow.go.cli.utils.helpers import app_callback
from latticeflow.go.cli.utils.helpers import get_client_from_env
from latticeflow.go.cli.utils.single_commands import with_callback


def register_switch_command(app: typer.Typer) -> None:
    app.command(
        name="switch",
        short_help="Switch AI app context",
        help=(
            "This command switches AI app context. All subsequent commands will be"
            " executed within the AI app context until switched to another. Command"
            " raises if the AI app with the specified key does not exist. AI app context is"
            " stored in a configuration file (default location is '~/.latticeflow/config.json')."
        ),
    )(with_callback(lambda: app_callback(get_cli_env_vars))(_switch))


def _switch(
    ai_app_key: str = typer.Argument(
        ..., help="The key of the AI app in context.", envvar=LF_APP_KEY_CONTEXT_NAME
    ),
) -> None:
    client = get_client_from_env()
    try:
        client.ai_apps.get_ai_app_by_key(ai_app_key)
        config, config_file = get_configuration_file()
        config[LF_APP_KEY_CONTEXT_NAME] = ai_app_key
        upsert_configuration_file(config_file, config)
        cli_print.log_info(f"AI app context saved to '{config_file}'.")
    except Exception as error:
        raise CLIError(
            "Failed to set the AI app in context. Please check the AI app with "
            f"key '{ai_app_key}' exists and try again."
        ) from error


def register_configure_command(app: typer.Typer) -> None:
    app.command(
        name="configure",
        short_help="Configure AI GO! CLI options",
        help=(
            "This command validates and stores the CLI options into a configuration "
            "file (default location is '~/.latticeflow/config.json')."
        ),
    )(_configure)


def _configure(
    url: str = typer.Option(
        ...,
        help="URL to your AI GO! deployment.",
        prompt="Enter your AI GO! URL (e.g. 'https://aigo.myorg.com')",
        envvar=LF_AIGO_URL_NAME,
    ),
    api_key: str = typer.Option(
        ...,
        "--api-key",
        help="Your AI GO! API Key.",
        prompt="Enter your AI GO! API Key (e.g. '8421d0210751e999ce6b9e5759985346')",
        envvar=LF_API_KEY_NAME,
    ),
    verify_ssl: bool = typer.Option(
        True,
        "--verify-ssl/--no-verify-ssl",
        help="Flag whether to verify SSL certificates.",
        envvar=LF_VERIFY_SSL_NAME,
    ),
) -> None:
    try:
        client = Client(base_url=url, api_key=api_key, verify_ssl=verify_ssl)
        client.users.get_users()
        config, config_file = get_configuration_file()
        config[LF_AIGO_URL_NAME] = url
        config[LF_API_KEY_NAME] = api_key
        config[LF_VERIFY_SSL_NAME] = verify_ssl
        upsert_configuration_file(config_file, config)
        cli_print.log_info(f"CLI option saved to '{config_file}'.")
    except Exception as error:
        raise CLIError(
            f"Failed to connect to AI GO! at '{url}'. Please check your details and "
            f"try again."
        ) from error


def register_status_command(app: typer.Typer) -> None:
    app.command(
        name="status",
        short_help="Shows the current AI app context and the saved AI GO! CLI options",
    )(_status)


def _status() -> None:
    config, config_file = get_configuration_file()
    ai_app_key = config.get(LF_APP_KEY_CONTEXT_NAME)
    url = config.get(LF_AIGO_URL_NAME)
    api_key = config.get(LF_API_KEY_NAME)
    cli_print.log_saved_ai_app_context(ai_app_key)
    cli_print.log_saved_cli_options(config_file, url, api_key)
