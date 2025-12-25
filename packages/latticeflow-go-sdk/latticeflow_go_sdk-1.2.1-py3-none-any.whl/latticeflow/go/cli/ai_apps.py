from __future__ import annotations

from pathlib import Path
from typing import Callable

import typer

import latticeflow.go.cli.utils.arguments as cli_args
import latticeflow.go.cli.utils.exceptions as cli_exc
import latticeflow.go.cli.utils.printing as cli_print
from latticeflow.go import Client
from latticeflow.go.cli.utils.dtypes import CLICreateAIApp
from latticeflow.go.cli.utils.helpers import create_single_entity
from latticeflow.go.cli.utils.helpers import dump_entity_to_yaml_file
from latticeflow.go.cli.utils.helpers import get_client_from_env
from latticeflow.go.cli.utils.helpers import get_files_at_path
from latticeflow.go.cli.utils.helpers import is_update_payload_same_as_existing_entity
from latticeflow.go.cli.utils.helpers import register_app_callback
from latticeflow.go.cli.utils.helpers import update_single_entity
from latticeflow.go.cli.utils.schema_mappers import EntityByIdentifiersMap
from latticeflow.go.cli.utils.schema_mappers import map_ai_app_api_to_cli_entity
from latticeflow.go.cli.utils.schema_mappers import map_ai_app_cli_to_api_entity
from latticeflow.go.cli.utils.yaml_utils import load_yaml_recursively
from latticeflow.go.models import AIApp
from latticeflow.go.models import StoredAIApp


PRETTY_ENTITY_NAME = "AI app"
TABLE_COLUMNS: list[tuple[str, Callable[[StoredAIApp], str]]] = [
    ("Key", lambda app: app.key),
    ("Name", lambda app: app.display_name),
]
ai_app_app = typer.Typer(help="AI app commands")
register_app_callback(ai_app_app)


@ai_app_app.command("list")
def list_ai_apps(is_json_output: bool = cli_args.json_flag_option) -> None:
    """List all AI apps as JSON or in a table."""
    if is_json_output:
        cli_print.suppress_logging()

    client = get_client_from_env()
    try:
        stored_ai_apps = client.ai_apps.get_ai_apps().ai_apps
        cli_ai_apps = [
            map_ai_app_api_to_cli_entity(stored_ai_app=stored_ai_app)
            for stored_ai_app in stored_ai_apps
        ]
        if is_json_output:
            cli_print.print_entities_as_json(cli_ai_apps)
        else:
            cli_print.print_table("AI apps", cli_ai_apps, TABLE_COLUMNS)
    except Exception as error:
        raise cli_exc.CLIListError(PRETTY_ENTITY_NAME) from error


@ai_app_app.command("add")
def _add(
    path: Path = cli_args.glob_config_path_option(PRETTY_ENTITY_NAME),
    should_validate_only: bool = cli_args.should_validate_only_option,
) -> None:
    """Create/update AI app(s) based on YAML configuration(s)."""
    if not (config_files := get_files_at_path(path)):
        raise cli_exc.CLIConfigNotFoundError(PRETTY_ENTITY_NAME, path)

    if should_validate_only:
        _validate_ai_apps(config_files)
        return

    client = get_client_from_env()
    ai_apps_map = EntityByIdentifiersMap(client.ai_apps.get_ai_apps().ai_apps)
    is_creating_single_entity = len(config_files) == 1
    failures = 0
    for config_file in config_files:
        try:
            cli_ai_app = _get_cli_ai_app_from_file(config_file)
            ai_app = map_ai_app_cli_to_api_entity(
                cli_ai_app=cli_ai_app, config_file=config_file
            )
            stored_ai_app = ai_apps_map.get_entity_by_key(cli_ai_app.key)
            new_stored_ai_app = create_or_update_single_ai_app(
                client, ai_app, stored_ai_app
            )
            ai_apps_map.update_entity(new_stored_ai_app)
        except Exception as error:
            failures += 1
            if is_creating_single_entity:
                raise cli_exc.CLICreateUpdateSingleEntityError(
                    PRETTY_ENTITY_NAME, config_file
                ) from error
            cli_print.log_create_update_fail_error(
                PRETTY_ENTITY_NAME, config_file, error
            )
    if failures == len(config_files):
        raise cli_exc.CLICreateUpdateAllFailedError(PRETTY_ENTITY_NAME, config_file)


@ai_app_app.command("delete")
def _delete(key: str = cli_args.delete_key_argument(PRETTY_ENTITY_NAME)) -> None:
    """Delete the AI app with the provided key."""
    client = get_client_from_env()
    try:
        cli_print.log_delete_attempt_info(PRETTY_ENTITY_NAME, key)
        client.ai_apps.delete_ai_app_by_key(key=key)
        cli_print.log_delete_success_info(PRETTY_ENTITY_NAME, key)
    except Exception as error:
        raise cli_exc.CLIDeleteError(PRETTY_ENTITY_NAME, key) from error


@ai_app_app.command("export")
def _export(
    key: str = cli_args.export_key_argument(PRETTY_ENTITY_NAME),
    output: Path | None = cli_args.export_output_path_option,
) -> None:
    """Export the AI app with the provided key to a file or print as JSON."""
    if not output:
        cli_print.suppress_logging()

    client = get_client_from_env()
    try:
        stored_ai_app = client.ai_apps.get_ai_app_by_key(key)
        cli_ai_app = map_ai_app_api_to_cli_entity(stored_ai_app=stored_ai_app)
        if output:
            dump_entity_to_yaml_file(output, cli_ai_app)
            cli_print.log_export_success_info(PRETTY_ENTITY_NAME, output, key)
        else:
            cli_print.print_entities_as_json(cli_ai_app)
    except Exception as error:
        raise cli_exc.CLIExportError(
            PRETTY_ENTITY_NAME, key, output_path=output
        ) from error


def _get_cli_ai_app_from_file(config_file: Path) -> CLICreateAIApp:
    try:
        loaded_dict, _ = load_yaml_recursively(config_file)
        return CLICreateAIApp.model_validate(loaded_dict, ignore_extra=False)
    except Exception as error:
        raise cli_exc.CLIInvalidConfigError(
            PRETTY_ENTITY_NAME, config_file, "ai-apps"
        ) from error


def create_or_update_single_ai_app(
    client: Client,
    ai_app: AIApp,
    stored_ai_app: StoredAIApp | None,
    verbosity: cli_print.Verbosity = "high",
) -> StoredAIApp:
    if stored_ai_app and is_update_payload_same_as_existing_entity(
        ai_app, stored_ai_app
    ):
        cli_print.log_no_change_info(
            PRETTY_ENTITY_NAME, ai_app.key, verbosity=verbosity
        )
        return stored_ai_app
    elif stored_ai_app:
        return update_single_ai_app(client, stored_ai_app, ai_app, verbosity)
    else:
        return create_single_ai_app(client, ai_app, verbosity)


def update_single_ai_app(
    client: Client,
    stored_ai_app: StoredAIApp,
    ai_app: AIApp,
    verbosity: cli_print.Verbosity,
) -> StoredAIApp:
    return update_single_entity(
        pretty_entity_name=PRETTY_ENTITY_NAME,
        update_fn=lambda: client.ai_apps.update_ai_app(stored_ai_app.id, ai_app),
        entity_identifier_value=stored_ai_app.key,
        verbosity=verbosity,
    )


def create_single_ai_app(
    client: Client, ai_app: AIApp, verbosity: cli_print.Verbosity
) -> StoredAIApp:
    return create_single_entity(
        pretty_entity_name=PRETTY_ENTITY_NAME,
        create_fn=lambda: client.ai_apps.create_ai_app(ai_app),
        entity_identifier_value=ai_app.key,
        verbosity=verbosity,
    )


def _validate_ai_apps(config_files: list[Path]) -> None:
    for config_file in config_files:
        try:
            _get_cli_ai_app_from_file(config_file)
            cli_print.log_validation_success_info(config_file)
        except Exception as error:
            raise cli_exc.CLIValidationError(PRETTY_ENTITY_NAME) from error
