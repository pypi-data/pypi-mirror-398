from __future__ import annotations

import datetime
import io
import zipfile
from pathlib import Path
from typing import Callable

import typer

import latticeflow.go.cli.utils.arguments as cli_args
import latticeflow.go.cli.utils.exceptions as cli_exc
import latticeflow.go.cli.utils.printing as cli_print
from latticeflow.go.cli.utils.helpers import get_client_from_env
from latticeflow.go.cli.utils.helpers import load_ai_app_key
from latticeflow.go.cli.utils.helpers import register_app_callback
from latticeflow.go.cli.utils.time import datetime_to_str
from latticeflow.go.cli.utils.time import timestamp_to_localized_datetime
from latticeflow.go.models import StoredEvaluation
from latticeflow.go.models import StoredTaskResult


def _get_progress(task_result: StoredTaskResult) -> str:
    progress = task_result.progress
    if progress is None:
        return ""

    if progress.num_total_samples is None or progress.num_processed_samples is None:
        return f"{progress.progress:.1%}"

    return f"{progress.progress:.1%} ({progress.num_processed_samples}/{progress.num_total_samples})"


def _get_runtime(task_result: StoredTaskResult) -> str:
    if task_result.started_at is not None and task_result.finished_at is not None:
        delta = datetime.timedelta(
            seconds=task_result.finished_at - task_result.started_at
        )
        return f"{delta}s"

    return "-"


PRETTY_ENTITY_NAME = "evaluation"
EVALUATION_TABLE_COLUMNS: list[tuple[str, Callable[[StoredEvaluation], str]]] = [
    ("ID", lambda evaluation: evaluation.id),
    ("Name", lambda evaluation: evaluation.display_name),
    ("Key", lambda evaluation: evaluation.key),
    (
        "Created",
        lambda evaluation: datetime_to_str(
            timestamp_to_localized_datetime(evaluation.created_at)
        ),
    ),
    ("Status", lambda evaluation: evaluation.execution_status.value),
]
TASK_RESULTS_TABLE_COLUMNS: list[tuple[str, Callable[[StoredTaskResult], str]]] = [
    ("Task Result ID", lambda task_result: task_result.id),
    ("Task Name", lambda task_result: task_result.display_name),
    ("Task Execution Status", lambda task_result: task_result.execution_status.value),
    (
        "Task Result Status",
        lambda task_result: task_result.result_status.value
        if task_result.result_status is not None
        else "-",
    ),
    ("Task Execution Progress", _get_progress),
    ("Task Execution Runtime", _get_runtime),
]
evaluation_app = typer.Typer(help="Evaluation commands")
register_app_callback(evaluation_app)


@evaluation_app.command("list")
def list_evaluations(is_json_output: bool = cli_args.json_flag_option) -> None:
    """List all evaluations as JSON or in a table."""
    if is_json_output:
        cli_print.suppress_logging()
    ai_app_key = load_ai_app_key()

    client = get_client_from_env()
    ai_app = client.ai_apps.get_ai_app_by_key(ai_app_key)
    try:
        stored_evaluations = client.evaluations.get_evaluations(
            app_id=ai_app.id
        ).evaluations
        if is_json_output:
            cli_print.print_entities_as_json(stored_evaluations)
        else:
            cli_print.print_table(
                "Evaluations", stored_evaluations, EVALUATION_TABLE_COLUMNS
            )
    except Exception as error:
        raise cli_exc.CLIListError(PRETTY_ENTITY_NAME) from error


@evaluation_app.command("overview")
def _overview(
    id: str = typer.Argument(
        ...,
        help=f"ID of the {PRETTY_ENTITY_NAME} for which the overview should be shown.",
    ),
    is_json_output: bool = cli_args.json_flag_option,
) -> None:
    """Show an overview of the evaluation with the provided ID for the provided AI App as JSON or in a table."""
    if is_json_output:
        cli_print.suppress_logging()
    ai_app_key = load_ai_app_key()

    client = get_client_from_env()

    ai_app = client.ai_apps.get_ai_app_by_key(ai_app_key)
    try:
        evaluation = client.evaluations.get_evaluation(
            app_id=ai_app.id, evaluation_id=id
        )
        if is_json_output:
            cli_print.print_entities_as_json(evaluation)
        else:
            cli_print.log_info(
                f"Evaluation ID: {id}\n"
                f"Evaluation Name: {evaluation.display_name}\n"
                f"Evaluation Key: {evaluation.key}\n"
                f"Status: {evaluation.execution_status.value}\n"
                f"Created at: {datetime_to_str(timestamp_to_localized_datetime(evaluation.created_at))}\n"
            )
            cli_print.print_table(
                f"Tasks results for evaluation with ID '{id}'",
                evaluation.task_results,
                TASK_RESULTS_TABLE_COLUMNS,
            )
    except Exception as error:
        raise cli_exc.CLIOverviewEvaluationError(id) from error


@evaluation_app.command("download")
def _download(
    id: str = typer.Argument(
        ...,
        help=f"ID of the {PRETTY_ENTITY_NAME} for which the "
        "results will be downloaded (as a ZIP file).",
    ),
    output: Path = typer.Option(
        ..., help="Path to output the ZIP file.", callback=cli_args.check_path_not_emtpy
    ),
) -> None:
    """Download the evaluation results as a ZIP file."""
    ai_app_key = load_ai_app_key()
    client = get_client_from_env()
    ai_app = client.ai_apps.get_ai_app_by_key(ai_app_key)
    try:
        results_zip_file = client.evaluations.download_evaluation_result(
            app_id=ai_app.id, evaluation_id=id
        )
    except Exception as error:
        raise cli_exc.CLIExportError(
            PRETTY_ENTITY_NAME, id, output_path=output
        ) from error

    output.mkdir(exist_ok=True, parents=True)
    zip_bytes = results_zip_file.payload.getbuffer()
    with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as zip_ref:
        zip_ref.extractall(output)

    cli_print.log_export_success_info(PRETTY_ENTITY_NAME, output, id)
