from __future__ import annotations

from pathlib import Path
from typing import Callable

import typer

import latticeflow.go.cli.utils.arguments as cli_args
import latticeflow.go.cli.utils.exceptions as cli_exc
import latticeflow.go.cli.utils.printing as cli_print
from latticeflow.go.cli.utils.dtypes import CLICreateDatasetGenerator
from latticeflow.go.cli.utils.helpers import create_single_entity
from latticeflow.go.cli.utils.helpers import dump_entity_to_yaml_file
from latticeflow.go.cli.utils.helpers import get_client_from_env
from latticeflow.go.cli.utils.helpers import get_files_at_path
from latticeflow.go.cli.utils.helpers import is_update_payload_same_as_existing_entity
from latticeflow.go.cli.utils.helpers import register_app_callback
from latticeflow.go.cli.utils.helpers import update_single_entity
from latticeflow.go.cli.utils.schema_mappers import EntityByIdentifiersMap
from latticeflow.go.cli.utils.schema_mappers import (
    map_dataset_generator_api_to_cli_entity,
)
from latticeflow.go.cli.utils.schema_mappers import (
    map_dataset_generator_cli_to_api_entity,
)
from latticeflow.go.cli.utils.yaml_utils import load_yaml_recursively
from latticeflow.go.client import Client
from latticeflow.go.models import DatasetGenerator
from latticeflow.go.models import StoredDatasetGenerator


PRETTY_ENTITY_NAME = "dataset generator"
TABLE_COLUMNS: list[tuple[str, Callable[[StoredDatasetGenerator], str]]] = [
    ("Key", lambda dataset_generator: dataset_generator.key),
    ("Name", lambda dataset_generator: dataset_generator.display_name),
]
dataset_generator_app = typer.Typer(help="Dataset generator commands")
register_app_callback(dataset_generator_app)


@dataset_generator_app.command("list")
def list_dataset_generators(is_json_output: bool = cli_args.json_flag_option) -> None:
    """List all dataset generators as JSON or in a table."""
    if is_json_output:
        cli_print.suppress_logging()

    client = get_client_from_env()
    try:
        stored_dataset_generators = (
            client.dataset_generators.get_dataset_generators().dataset_generators
        )
        datasets_map = EntityByIdentifiersMap(client.datasets.get_datasets().datasets)
        models_map = EntityByIdentifiersMap(client.models.get_models().models)
        cli_dataset_generators = [
            map_dataset_generator_api_to_cli_entity(
                stored_dataset_generator=stored_dataset_generator,
                datasets_map=datasets_map,
                models_map=models_map,
            )
            for stored_dataset_generator in stored_dataset_generators
        ]

        if is_json_output:
            cli_print.print_entities_as_json(cli_dataset_generators)
        else:
            cli_print.print_table(
                "Dataset generators", cli_dataset_generators, TABLE_COLUMNS
            )
    except Exception as error:
        raise cli_exc.CLIListError(PRETTY_ENTITY_NAME) from error


@dataset_generator_app.command("add")
def _add(
    path: Path = cli_args.glob_config_path_option(PRETTY_ENTITY_NAME),
    should_validate_only: bool = cli_args.should_validate_only_option,
) -> None:
    """Create/update dataset generator(s) based on YAML configuration(s)."""
    if not (config_files := get_files_at_path(path)):
        raise cli_exc.CLIConfigNotFoundError(PRETTY_ENTITY_NAME, path)

    if should_validate_only:
        _validate_dataset_generators(config_files)
        return

    client = get_client_from_env()
    dataset_generators_map = EntityByIdentifiersMap(
        client.dataset_generators.get_dataset_generators().dataset_generators
    )
    datasets_map = EntityByIdentifiersMap(client.datasets.get_datasets().datasets)
    models_map = EntityByIdentifiersMap(client.models.get_models().models)
    is_creating_single_entity = len(config_files) == 1
    failures = 0
    for config_file in config_files:
        try:
            cli_dataset_generator = _get_cli_dataset_generator_from_file(config_file)
            dataset_generator = map_dataset_generator_cli_to_api_entity(
                cli_dataset_generator=cli_dataset_generator,
                datasets_map=datasets_map,
                models_map=models_map,
                config_file=config_file,
            )
            stored_dataset_generator = dataset_generators_map.get_entity_by_key(
                dataset_generator.key
            )
            new_stored_dataset_generator = create_or_update_single_dataset_generator(
                client, dataset_generator, stored_dataset_generator
            )
            dataset_generators_map.update_entity(new_stored_dataset_generator)
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


@dataset_generator_app.command("delete")
def _delete(key: str = cli_args.delete_key_argument(PRETTY_ENTITY_NAME)) -> None:
    """Delete the dataset generator with the provided key."""
    client = get_client_from_env()
    try:
        cli_print.log_delete_attempt_info(PRETTY_ENTITY_NAME, key)
        client.dataset_generators.delete_dataset_generator_by_key(key=key)
        cli_print.log_delete_success_info(PRETTY_ENTITY_NAME, key)
    except Exception as error:
        raise cli_exc.CLIDeleteError(PRETTY_ENTITY_NAME, key) from error


@dataset_generator_app.command("export")
def _export(
    key: str = cli_args.export_key_argument(PRETTY_ENTITY_NAME),
    output: Path | None = cli_args.export_output_path_option,
) -> None:
    """Export the dataset generator with the provided key to a file or print as JSON."""
    if not output:
        cli_print.suppress_logging()

    client = get_client_from_env()
    try:
        stored_dataset_generator = (
            client.dataset_generators.get_dataset_generator_by_key(key)
        )
        cli_dataset_generator = map_dataset_generator_api_to_cli_entity(
            stored_dataset_generator=stored_dataset_generator,
            datasets_map=EntityByIdentifiersMap(
                client.datasets.get_datasets().datasets
            ),
            models_map=EntityByIdentifiersMap(client.models.get_models().models),
        )
        if output:
            dump_entity_to_yaml_file(output, cli_dataset_generator)
            cli_print.log_export_success_info(PRETTY_ENTITY_NAME, output, key)
        else:
            cli_print.print_entities_as_json(cli_dataset_generator)
    except Exception as error:
        raise cli_exc.CLIExportError(
            PRETTY_ENTITY_NAME, key, output_path=output
        ) from error


def _get_cli_dataset_generator_from_file(
    config_file: Path,
) -> CLICreateDatasetGenerator:
    try:
        loaded_dict, _ = load_yaml_recursively(config_file)
        return CLICreateDatasetGenerator.model_validate(loaded_dict, ignore_extra=False)
    except Exception as error:
        raise cli_exc.CLIInvalidConfigError(
            PRETTY_ENTITY_NAME, config_file, "dataset-generators"
        ) from error


def create_or_update_single_dataset_generator(
    client: Client,
    dataset_generator: DatasetGenerator,
    stored_dataset_generator: StoredDatasetGenerator | None,
    verbosity: cli_print.Verbosity = "high",
) -> StoredDatasetGenerator:
    if stored_dataset_generator and is_update_payload_same_as_existing_entity(
        dataset_generator, stored_dataset_generator
    ):
        cli_print.log_no_change_info(
            PRETTY_ENTITY_NAME, dataset_generator.key, verbosity=verbosity
        )
        return stored_dataset_generator
    elif stored_dataset_generator:
        return update_single_dataset_generator(
            client, stored_dataset_generator, dataset_generator, verbosity
        )
    else:
        return create_single_dataset_generator(client, dataset_generator, verbosity)


def update_single_dataset_generator(
    client: Client,
    stored_dataset_generator: StoredDatasetGenerator,
    dataset_generator: DatasetGenerator,
    verbosity: cli_print.Verbosity,
) -> StoredDatasetGenerator:
    return update_single_entity(
        pretty_entity_name=PRETTY_ENTITY_NAME,
        update_fn=lambda: client.dataset_generators.update_dataset_generator(
            stored_dataset_generator.id, dataset_generator
        ),
        entity_identifier_value=stored_dataset_generator.key,
        verbosity=verbosity,
    )


def create_single_dataset_generator(
    client: Client, dataset_generator: DatasetGenerator, verbosity: cli_print.Verbosity
) -> StoredDatasetGenerator:
    return create_single_entity(
        pretty_entity_name=PRETTY_ENTITY_NAME,
        create_fn=lambda: client.dataset_generators.create_dataset_generator(
            dataset_generator
        ),
        entity_identifier_value=dataset_generator.key,
        verbosity=verbosity,
    )


def _validate_dataset_generators(config_files: list[Path]) -> None:
    for config_file in config_files:
        try:
            _get_cli_dataset_generator_from_file(config_file)
            cli_print.log_validation_success_info(config_file)
        except Exception as error:
            raise cli_exc.CLIValidationError(PRETTY_ENTITY_NAME) from error
