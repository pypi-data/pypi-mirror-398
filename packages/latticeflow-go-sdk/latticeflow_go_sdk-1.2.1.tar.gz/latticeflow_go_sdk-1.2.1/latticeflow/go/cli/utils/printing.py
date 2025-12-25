from __future__ import annotations

import json
import logging  # noqa: TID251
import shutil
from pathlib import Path
from typing import Any
from typing import Callable
from typing import Literal
from typing import Sequence

import httpcore
import httpx
import typer
import yaml
from rich.console import Console
from rich.table import Table

from latticeflow.go.cli.utils.constants import LF_API_TIMEOUT_NAME
from latticeflow.go.cli.utils.yaml_utils import yaml_safe_dump_pretty
from latticeflow.go.models import LFBaseModel
from latticeflow.go.types import ApiError


Verbosity = Literal["low", "high"]


class TyperHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        fg = None
        bg = None

        if record.levelno == logging.INFO:
            fg = typer.colors.BRIGHT_BLUE
        elif record.levelno == logging.WARNING:
            fg = typer.colors.YELLOW
        elif record.levelno == logging.ERROR:
            fg = typer.colors.RED

        typer.secho(self.format(record), fg=fg, bg=bg)


def configure_logging() -> None:
    typer_handler = TyperHandler()
    typer_handler.setFormatter(logging.Formatter("%(message)s"))
    logging.basicConfig(level=logging.INFO, handlers=[typer_handler], force=True)
    logging.getLogger("httpx").setLevel(logging.WARNING)


def suppress_logging() -> None:
    logging.disable(logging.WARNING)


def log_warning(warning: str) -> None:
    """Logs an info message to stdout.
    Is suppressed if ``suppress_logging`` was called before."""
    logging.warning(warning)


def log_info(info: str) -> None:
    """Logs an info message to stdout.
    Is suppressed if ``suppress_logging`` was called before."""
    logging.info(info)


def log_error(error: str) -> None:
    """Logs an error message to stdout.
    Is NOT suppressed if ``suppress_logging`` was called before."""
    logging.error(error)


def log_dict(title: str, data: dict[str, Any]) -> None:
    """Logs the title and the data as an info message to stdout.
    Is suppressed if ``suppress_logging`` was called before."""
    try:
        data_str = yaml_safe_dump_pretty(data)
    except yaml.YAMLError:
        data_str = str(data)
    log_info(f"{title}\n\n{data_str}")


def log_list_dicts(title: str, data: list[dict[str, Any]]) -> None:
    """Logs the title and the data as an info message to stdout.
    Is suppressed if ``suppress_logging`` was called before."""
    try:
        data_str = yaml_safe_dump_pretty(data)
    except yaml.YAMLError:
        data_str = str(data)
    log_info(f"{title}\n\n{data_str}")


def print_table(
    title: str, rows: Sequence[Any], columns: Sequence[tuple[str, Callable[[Any], str]]]
) -> None:
    console = Console()
    table = Table(
        title=f"{title} ({len(rows)} row{'s' if len(rows) != 1 else ''})", min_width=87
    )
    for header, _ in columns:
        table.add_column(header)

    for row in rows:
        cells = []
        for _, get in columns:
            v = get(row)
            cells.append("" if v is None else str(v))
        table.add_row(*cells)

    console.print(table)


def print_json(content: Any) -> None:
    print(json.dumps(content, indent=2))  # noqa: T201


def print_entities_as_json(
    single_entity_or_list: LFBaseModel | Sequence[LFBaseModel],
) -> None:
    if isinstance(single_entity_or_list, Sequence):
        print_json([entity.model_dump(mode="json") for entity in single_entity_or_list])
    else:
        print_json(single_entity_or_list.model_dump(mode="json"))


def log_char_full_width(char: str) -> None:
    width = shutil.get_terminal_size((80, 20)).columns
    logging.info(char * width)


def log_no_change_info(
    entity_name: str,
    identifier_value: str,
    identifier_type: str = "key",
    *,
    verbosity: Verbosity,
) -> None:
    if verbosity == "low":
        log_info(
            f'[{entity_name.capitalize()}({identifier_type}="{identifier_value}")] Skipped (no changes detected)'
        )
    elif verbosity == "high":
        log_info(
            f"Skipping the update of {entity_name} with {identifier_type} '{identifier_value}'"
            " because the data did not change."
        )


def log_update_attempt_info(
    entity_name: str,
    identifier_value: str,
    identifier_type: str = "key",
    *,
    verbosity: Verbosity,
) -> None:
    if verbosity == "high":
        log_info(
            f"Trying to update {entity_name} with {identifier_type} '{identifier_value}'."
        )


def log_update_success_info(
    entity_name: str,
    identifier_value: str,
    identifier_type: str = "key",
    *,
    verbosity: Verbosity,
) -> None:
    if verbosity == "low":
        log_info(
            f'[{entity_name.capitalize()}({identifier_type}="{identifier_value}")] Updated successfully'
        )
    elif verbosity == "high":
        log_info(
            f"Successfully updated {entity_name} with {identifier_type} '{identifier_value}'."
        )


def log_test_success_info(
    entity_name: str, identifier_value: str, identifier_type: str = "key"
) -> None:
    log_info(
        f"Successfully tested configuration of {entity_name} with {identifier_type} '{identifier_value}'."
    )


def log_create_attempt_info(
    entity_name: str,
    identifier_value: str | None,
    identifier_type: str | None = "key",
    *,
    verbosity: Verbosity,
) -> None:
    if verbosity == "high":
        identifier_suffix = (
            f" with {identifier_type} '{identifier_value}'"
            if (identifier_type and identifier_value)
            else ""
        )
        log_info(f"Trying to create {entity_name}{identifier_suffix}.")


def log_create_success_info(
    entity_name: str,
    identifier_value: str | None,
    identifier_type: str | None = "key",
    *,
    verbosity: Verbosity,
) -> None:
    if verbosity == "low":
        identifier_suffix = (
            f'({identifier_type}="{identifier_value}")'
            if (identifier_type and identifier_value)
            else ""
        )
        log_info(
            f"[{entity_name.capitalize()}{identifier_suffix}] Created successfully"
        )
    elif verbosity == "high":
        identifier_suffix = (
            f" with {identifier_type} '{identifier_value}'"
            if (identifier_type and identifier_value)
            else ""
        )
        log_info(f"Successfully created {entity_name}{identifier_suffix}.")


def log_delete_attempt_info(
    entity_name: str, identifier_value: str, identifier_type: str = "key"
) -> None:
    log_info(
        f"Trying to delete {entity_name} with {identifier_type} '{identifier_value}'."
    )


def log_delete_success_info(
    entity_name: str, identifier_value: str, identifier_type: str = "key"
) -> None:
    log_info(
        f"Successfully deleted {entity_name} with {identifier_type} '{identifier_value}'."
    )


def log_export_success_info(
    entity_name: str,
    output_path: Path,
    identifier_value: str,
    identifier_type: str = "key",
) -> None:
    log_info(
        f"Exported {entity_name} with {identifier_type} '{identifier_value}' to '{output_path}'."
    )


def log_create_update_fail_error(
    entity_name: str, path: Path | None, error: Exception
) -> None:
    path_suffix = f" from path '{path}'" if path else ""
    log_error(f"Could not create/update {entity_name}{path_suffix}:\n")
    log_error(summarize_exception_chain(error))


def log_model_already_integrated_info(
    provider: str, model_key_from_provider: str, model_key: str, *, verbosity: Verbosity
) -> None:
    if verbosity == "low":
        log_info(f'[Model(key="{model_key}")] Already integrated')
    elif verbosity == "high":
        log_info(
            f"Model '{model_key_from_provider}' from provider '{provider}'"
            f" already integrated. You can reference it by the key '{model_key}'."
        )


def log_model_integration_success_info(
    provider: str, model_key_from_provider: str, model_key: str, *, verbosity: Verbosity
) -> None:
    if verbosity == "low":
        log_info(f'[Model(key="{model_key}")] Integrated successfully')
    elif verbosity == "high":
        log_info(
            f"Successfully integrated model '{model_key_from_provider}' from"
            f" provider '{provider}'. You can reference it by the key '{model_key}'."
        )


def log_saved_ai_app_context(ai_app_key: str | None) -> None:
    if ai_app_key:
        log_info(f"Working on AI app with key '{ai_app_key}'.")
    else:
        log_info("No AI app in context. Please run `lf switch 'my-app'`.")


def log_saved_cli_options(
    config_path: Path, url: str | None, api_key: str | None
) -> None:
    if url is not None:
        log_info(f"AI GO! URL: {url}")
    else:
        log_info("AI GO! URL is not set.")

    if api_key is not None:
        log_info(f"AI GO! API Key: ****{api_key[-4:]}")
    else:
        log_info("AI GO! API Key is not set.")

    log_info(
        f"\nYou can see your saved configuration at '{config_path}'."
        "\nTo update it, run the `lf configure` command again."
    )


def log_creating_or_updating_entities_info(entity_name: str, path: Path) -> None:
    log_info(
        f"Creating/updating {entity_name} entities from the run config at path '{path}'."
    )


def log_validation_fail_error(path: Path, error: Exception) -> None:
    log_error(
        f"Validation failed for configuration at path '{path}'."
        f"\n{summarize_exception_chain(error)}\n\n"
    )


def log_validation_success_info(path: Path) -> None:
    log_info(f"Successfully validated configuration at path '{path}'.")


def log_current_app_context_info(ai_app_key: str) -> None:
    log_info(f"On AI app '{ai_app_key}'.")


def _format_error(e: BaseException) -> str:
    if isinstance(e, ApiError):
        return f"API error: {e.error.message}"
    if isinstance(e, httpx.TimeoutException) or isinstance(
        e, httpcore.TimeoutException
    ):
        return (
            "Timeout error: Could not connect to the API before timeout. "
            "Check whether it is available and whether your configuration is correct.\n"
            "If long operations are expected, consider increasing the timeout value by "
            f"setting the `{LF_API_TIMEOUT_NAME}` environment variable."
        )
    return f"{type(e).__name__}: {str(e)}"


def summarize_exception_chain(exception: BaseException) -> str:
    """Extracts the messages of the provided exception and all its children."""
    messages: list[str] = []
    previous_message = ""
    while True:
        message = _format_error(exception)
        # Avoid repetitions.
        if message != previous_message:
            messages.append(message)
            previous_message = message

        # Reference: https://docs.python.org/3/library/exceptions.html#exception-context
        if exception.__cause__ is not None:
            exception = exception.__cause__
        elif exception.__context__ is not None and not exception.__suppress_context__:
            exception = exception.__context__
        else:
            break

    return "\n\n".join(messages)
