from __future__ import annotations

from pathlib import Path
from typing import Callable

import typer
import yaml

import latticeflow.go.cli.utils.arguments as cli_args
import latticeflow.go.cli.utils.exceptions as cli_exc
import latticeflow.go.cli.utils.printing as cli_print
from latticeflow.go import Client
from latticeflow.go.cli.utils.dtypes import CLICreateTask
from latticeflow.go.cli.utils.helpers import create_single_entity
from latticeflow.go.cli.utils.helpers import dump_entity_to_yaml_file
from latticeflow.go.cli.utils.helpers import get_client_from_env
from latticeflow.go.cli.utils.helpers import get_files_at_path
from latticeflow.go.cli.utils.helpers import is_update_payload_same_as_existing_entity
from latticeflow.go.cli.utils.helpers import register_app_callback
from latticeflow.go.cli.utils.helpers import update_single_entity
from latticeflow.go.cli.utils.schema_mappers import EntityByIdentifiersMap
from latticeflow.go.cli.utils.schema_mappers import map_config_keys_to_ids
from latticeflow.go.cli.utils.schema_mappers import map_task_api_to_cli_entity
from latticeflow.go.cli.utils.schema_mappers import map_task_cli_to_api_entity
from latticeflow.go.cli.utils.yaml_utils import load_yaml_recursively
from latticeflow.go.models import StoredTask
from latticeflow.go.models import Task
from latticeflow.go.models import TaskResultError
from latticeflow.go.models import TaskResultErrorStage
from latticeflow.go.models import TaskTestRequest
from latticeflow.go.models import TaskTestResult


PRETTY_ENTITY_NAME = "task"
TABLE_COLUMNS: list[tuple[str, Callable[[StoredTask], str]]] = [
    ("Key", lambda task: task.key),
    ("Entity type", lambda task: task.evaluated_entity_type.value),
]
task_app = typer.Typer(help="Task commands")
register_app_callback(task_app)


@task_app.command("list")
def list_tasks(
    is_json_output: bool = cli_args.json_flag_option,
    should_list_all: bool = cli_args.should_list_all_option(PRETTY_ENTITY_NAME),
) -> None:
    """List all tasks as JSON or in a table."""
    if is_json_output:
        cli_print.suppress_logging()

    client = get_client_from_env()
    try:
        stored_tasks = client.tasks.get_tasks(user_only=not should_list_all).tasks
        models_map = EntityByIdentifiersMap(client.models.get_models().models)
        datasets_map = EntityByIdentifiersMap(client.datasets.get_datasets().datasets)
        cli_tasks = [
            map_task_api_to_cli_entity(
                stored_task=stored_task,
                models_map=models_map,
                datasets_map=datasets_map,
            )
            for stored_task in stored_tasks
        ]
        if is_json_output:
            cli_print.print_entities_as_json(cli_tasks)
        else:
            cli_print.print_table("Tasks", cli_tasks, TABLE_COLUMNS)
    except Exception as error:
        raise cli_exc.CLIListError(PRETTY_ENTITY_NAME) from error


@task_app.command("add")
def _add(
    path: Path = cli_args.glob_config_path_option(PRETTY_ENTITY_NAME),
    should_validate_only: bool = cli_args.should_validate_only_option,
) -> None:
    """Create/update task(s) based on YAML configuration(s)."""
    if not (config_files := get_files_at_path(path)):
        raise cli_exc.CLIConfigNotFoundError(PRETTY_ENTITY_NAME, path)

    if should_validate_only:
        _validate_tasks(config_files)
        return

    client = get_client_from_env()
    tasks_map = EntityByIdentifiersMap(client.tasks.get_tasks().tasks)
    models_map = EntityByIdentifiersMap(client.models.get_models().models)
    datasets_map = EntityByIdentifiersMap(client.datasets.get_datasets().datasets)
    is_creating_single_entity = len(config_files) == 1
    failures = 0
    for config_file in config_files:
        try:
            cli_task = _get_cli_task_from_file(config_file)
            task = map_task_cli_to_api_entity(
                cli_task=cli_task,
                models_map=models_map,
                datasets_map=datasets_map,
                config_file=config_file,
            )
            stored_task = tasks_map.get_entity_by_key(task.key)
            new_stored_task = create_or_update_single_task(client, task, stored_task)
            tasks_map.update_entity(new_stored_task)
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


@task_app.command("delete")
def _delete(key: str = cli_args.delete_key_argument(PRETTY_ENTITY_NAME)) -> None:
    """Delete the task with the provided key."""
    client = get_client_from_env()
    try:
        cli_print.log_delete_attempt_info(PRETTY_ENTITY_NAME, key)
        client.tasks.delete_task_by_key(key=key, delete_evaluations=False)
        cli_print.log_delete_success_info(PRETTY_ENTITY_NAME, key)
    except Exception as error:
        raise cli_exc.CLIDeleteError(PRETTY_ENTITY_NAME, key) from error


@task_app.command("export")
def _export(
    key: str = cli_args.export_key_argument(PRETTY_ENTITY_NAME),
    output: Path | None = cli_args.export_output_path_option,
) -> None:
    """Export the task with the provided key to a file or print as JSON."""
    if not output:
        cli_print.suppress_logging()

    client = get_client_from_env()
    try:
        stored_task = client.tasks.get_task_by_key(key=key)
        cli_task = map_task_api_to_cli_entity(
            stored_task=stored_task,
            models_map=EntityByIdentifiersMap(client.models.get_models().models),
            datasets_map=EntityByIdentifiersMap(
                client.datasets.get_datasets().datasets
            ),
        )
        if output:
            dump_entity_to_yaml_file(output, cli_task)
            cli_print.log_export_success_info(PRETTY_ENTITY_NAME, output, key)
        else:
            cli_print.print_entities_as_json(cli_task)
    except Exception as error:
        raise cli_exc.CLIExportError(
            PRETTY_ENTITY_NAME, key, output_path=output
        ) from error


@task_app.command("test")
def _test(
    key: str = cli_args.test_configuration_key_argument(PRETTY_ENTITY_NAME),
    config_file: Path | None = typer.Option(
        None,
        "--config",
        help="Path to a YAML file containing the configuration of the task. If "
        "not provided, an empty configuration will be used.",
        callback=cli_args.check_path_not_emtpy,
    ),
    model_key: str = typer.Option(
        ..., "--model-key", help="The key of the model to test the task with."
    ),
    # TODO: Allow specifying sample indices?
    num_samples: int = typer.Option(
        1, "--num-samples", "-n", help="The number of samples to test the task with."
    ),
) -> None:
    """Test the task with the provided key on a few samples."""
    client = get_client_from_env(read_timeout=60.0)
    try:
        stored_task = client.tasks.get_task_by_key(key)
    except Exception as error:
        raise cli_exc.CLITestConfigurationError(PRETTY_ENTITY_NAME, key) from error

    try:
        task_config = _get_task_test_config_from_path(config_file, stored_task, client)
    except Exception as error:
        raise cli_exc.CLIInvalidConfigError(
            PRETTY_ENTITY_NAME, config_file, None
        ) from error

    cli_print.log_info(
        f"Testing task '{key}' with model '{model_key}' on {num_samples} sample(s) ..."
    )
    try:
        task_test_result = client.tasks.test_task(
            stored_task.id,
            TaskTestRequest(
                config=task_config,
                entity_id=client.models.get_model_by_key(model_key).id,
                sample_indices=list(range(num_samples)),
            ),
        )
        _display_test_results(task_test_result, key)
    except Exception as error:
        raise cli_exc.CLITestConfigurationError(PRETTY_ENTITY_NAME, key) from error


def _log_task_result_error(error: TaskResultError) -> None:
    if error.stage is None:
        cli_print.log_warning("Encountered error:")
    else:
        cli_print.log_warning(f"Encountered error during {error.stage.value} stage:")
    cli_print.log_warning(error.error_type)
    if error.message:
        cli_print.log_warning(error.message)
    if error.hint:
        cli_print.log_warning(error.hint)


def _get_cli_task_from_file(config_file: Path) -> CLICreateTask:
    try:
        loaded_dict, _ = load_yaml_recursively(config_file)
        return CLICreateTask.model_validate(loaded_dict, ignore_extra=False)
    except Exception as error:
        raise cli_exc.CLIInvalidConfigError(
            PRETTY_ENTITY_NAME, config_file, "tasks"
        ) from error


def _display_test_results(task_test_result: TaskTestResult, task_key: str) -> None:
    cli_print.log_info("Checking configuration")
    if (
        task_test_result.error is not None
        and task_test_result.error.stage == TaskResultErrorStage.CONFIGURATION
    ):
        _log_task_result_error(task_test_result.error)
    else:
        cli_print.log_info("Configuration is valid.")

    if task_test_result.sample_results is not None:
        cli_print.log_char_full_width("=")
        num_failed_samples = 0
        for sample_index, sample_result in enumerate(
            task_test_result.sample_results, 1
        ):
            cli_print.log_info(
                f"Processing sample {sample_index}/{len(task_test_result.sample_results)}"
            )
            cli_print.log_char_full_width("-")
            if sample_result.sample is not None:
                cli_print.log_dict("Dataset sample", sample_result.sample)
                cli_print.log_char_full_width("-")
            if sample_result.solver_output is not None:
                cli_print.log_dict("Solver", sample_result.solver_output)
                cli_print.log_char_full_width("-")
            if sample_result.scores is not None:
                cli_print.log_list_dicts("Scores", sample_result.scores)
                cli_print.log_char_full_width("-")
            if sample_result.error is not None:
                _log_task_result_error(sample_result.error)
                cli_print.log_char_full_width("-")
                num_failed_samples += 1
        if num_failed_samples == 0:
            cli_print.log_info("Processed all samples.")
        else:
            cli_print.log_info(
                f"Processed all samples "
                f"({num_failed_samples}/{len(task_test_result.sample_results)} failed)."
            )
        cli_print.log_char_full_width("=")

    if task_test_result.metrics is not None:
        cli_print.log_dict("Metrics", task_test_result.metrics)
        cli_print.log_char_full_width("-")

    if (
        task_test_result.error is not None
        and task_test_result.error.stage != TaskResultErrorStage.CONFIGURATION
    ):
        _log_task_result_error(task_test_result.error)
    elif task_test_result.sample_results is not None:
        cli_print.log_test_success_info(PRETTY_ENTITY_NAME, task_key)


def _get_task_test_config_from_path(
    config_file: Path | None, stored_task: StoredTask, client: Client
) -> dict:
    if config_file is None:
        return {}

    if not config_file.is_file():
        raise cli_exc.CLIInvalidSingleFilePathError(config_file)

    return map_config_keys_to_ids(
        config_dict=yaml.safe_load(config_file.read_text()),
        config_spec=stored_task.config_spec,
        models_map=EntityByIdentifiersMap(client.models.get_models().models),
        datasets_map=EntityByIdentifiersMap(client.datasets.get_datasets().datasets),
        config_file=config_file,
    )


def create_or_update_single_task(
    client: Client,
    task: Task,
    stored_task: StoredTask | None,
    verbosity: cli_print.Verbosity = "high",
) -> StoredTask:
    if stored_task and is_update_payload_same_as_existing_entity(task, stored_task):
        cli_print.log_no_change_info(PRETTY_ENTITY_NAME, task.key, verbosity=verbosity)
        return stored_task
    elif stored_task:
        return update_single_task(client, stored_task, task, verbosity)
    else:
        return create_single_task(client, task, verbosity)


def update_single_task(
    client: Client, stored_task: StoredTask, task: Task, verbosity: cli_print.Verbosity
) -> StoredTask:
    return update_single_entity(
        pretty_entity_name=PRETTY_ENTITY_NAME,
        update_fn=lambda: client.tasks.update_task(
            stored_task.id, task, invalidate_evaluations=False
        ),
        entity_identifier_value=stored_task.key,
        verbosity=verbosity,
    )


def create_single_task(
    client: Client, task: Task, verbosity: cli_print.Verbosity
) -> StoredTask:
    return create_single_entity(
        pretty_entity_name=PRETTY_ENTITY_NAME,
        create_fn=lambda: client.tasks.create_task(task),
        entity_identifier_value=task.key,
        verbosity=verbosity,
    )


def _validate_tasks(config_files: list[Path]) -> None:
    for config_file in config_files:
        try:
            _get_cli_task_from_file(config_file)
            cli_print.log_validation_success_info(config_file)
        except Exception as error:
            raise cli_exc.CLIValidationError(PRETTY_ENTITY_NAME) from error
