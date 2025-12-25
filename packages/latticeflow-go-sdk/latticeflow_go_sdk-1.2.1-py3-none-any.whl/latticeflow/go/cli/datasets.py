from __future__ import annotations

import os
from operator import itemgetter
from pathlib import Path
from typing import Callable
from typing import cast

import typer

import latticeflow.go.cli.utils.arguments as cli_args
import latticeflow.go.cli.utils.exceptions as cli_exc
import latticeflow.go.cli.utils.printing as cli_print
from latticeflow.go.cli.utils.dtypes import CLICreateDataset
from latticeflow.go.cli.utils.helpers import dump_entity_to_yaml_file
from latticeflow.go.cli.utils.helpers import get_client_from_env
from latticeflow.go.cli.utils.helpers import get_files_at_path
from latticeflow.go.cli.utils.helpers import is_update_payload_same_as_existing_entity
from latticeflow.go.cli.utils.helpers import register_app_callback
from latticeflow.go.cli.utils.jsonl_utils import download_jsonl_data_from_client
from latticeflow.go.cli.utils.jsonl_utils import parse_jsonl
from latticeflow.go.cli.utils.jsonl_utils import save_jsonl_data_as_csv_or_jsonl
from latticeflow.go.cli.utils.schema_mappers import EntityByIdentifiersMap
from latticeflow.go.cli.utils.schema_mappers import map_dataset_api_to_cli_entity
from latticeflow.go.cli.utils.schema_mappers import map_dataset_cli_to_api_entity
from latticeflow.go.cli.utils.yaml_utils import load_yaml_recursively
from latticeflow.go.client import Client
from latticeflow.go.models import Dataset
from latticeflow.go.models import DatasetGenerationRequest
from latticeflow.go.models import DatasetMetadata
from latticeflow.go.models import ExecutionStatus
from latticeflow.go.models import GeneratedDataset
from latticeflow.go.models import StoredDataset
from latticeflow.go.utils.resolution import YAMLOriginInfo


PRETTY_ENTITY_NAME = "dataset"
TABLE_COLUMNS: list[tuple[str, Callable[[StoredDataset], str]]] = [
    ("Key", lambda dataset: dataset.key),
    ("Name", lambda dataset: dataset.display_name),
]

dataset_app = typer.Typer(help="Dataset commands")
register_app_callback(dataset_app)


@dataset_app.command("list")
def list_datasets(
    is_json_output: bool = cli_args.json_flag_option,
    should_list_all: bool = cli_args.should_list_all_option(PRETTY_ENTITY_NAME),
) -> None:
    """List all datasets as JSON or in a table."""
    if is_json_output:
        cli_print.suppress_logging()

    client = get_client_from_env()
    try:
        stored_datasets = client.datasets.get_datasets(
            user_only=not should_list_all
        ).datasets
        models_map = EntityByIdentifiersMap(client.models.get_models().models)
        datasets_map = EntityByIdentifiersMap(stored_datasets)
        dataset_generators_map = EntityByIdentifiersMap(
            client.dataset_generators.get_dataset_generators().dataset_generators
        )
        cli_datasets = [
            map_dataset_api_to_cli_entity(
                stored_dataset=stored_dataset,
                data_output=None,
                models_map=models_map,
                datasets_map=datasets_map,
                dataset_generators_map=dataset_generators_map,
            )
            for stored_dataset in stored_datasets
        ]
        if is_json_output:
            cli_print.print_entities_as_json(cli_datasets)
        else:
            cli_print.print_table("Datasets", cli_datasets, TABLE_COLUMNS)
    except Exception as error:
        raise cli_exc.CLIListError(PRETTY_ENTITY_NAME) from error


@dataset_app.command("add")
def _add(
    path: Path = cli_args.glob_config_path_option(PRETTY_ENTITY_NAME),
    should_validate_only: bool = cli_args.should_validate_only_option,
) -> None:
    """Create/update dataset(s) based on YAML configuration(s)."""
    if not (config_files := get_files_at_path(path)):
        raise cli_exc.CLIConfigNotFoundError(PRETTY_ENTITY_NAME, path)

    if should_validate_only:
        _validate_datasets(config_files)
        return

    client = get_client_from_env()
    models_map = EntityByIdentifiersMap(client.models.get_models().models)
    datasets_map = EntityByIdentifiersMap(client.datasets.get_datasets().datasets)
    dataset_generators_map = EntityByIdentifiersMap(
        client.dataset_generators.get_dataset_generators().dataset_generators
    )
    is_creating_single_entity = len(config_files) == 1
    failures = 0
    for config_file in config_files:
        try:
            cli_dataset, origin_info = _get_cli_dataset_from_file(config_file)
            (dataset, dataset_file_path, dataset_generation_request_with_id) = (
                map_dataset_cli_to_api_entity(
                    cli_dataset=cli_dataset,
                    models_map=models_map,
                    datasets_map=datasets_map,
                    dataset_generators_map=dataset_generators_map,
                    origin_info=origin_info,
                )
            )
            stored_dataset = datasets_map.get_entity_by_key(cli_dataset.key)
            new_stored_dataset = create_or_update_single_dataset(
                client,
                dataset,
                dataset_file_path,
                dataset_generation_request_with_id,
                stored_dataset,
            )
            datasets_map.update_entity(new_stored_dataset)
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


@dataset_app.command("delete")
def _delete(key: str = cli_args.delete_key_argument(PRETTY_ENTITY_NAME)) -> None:
    """Delete the dataset with the provided key."""
    client = get_client_from_env()
    try:
        cli_print.log_delete_attempt_info(PRETTY_ENTITY_NAME, key)
        client.datasets.delete_dataset_by_key(key=key)
        cli_print.log_delete_success_info(PRETTY_ENTITY_NAME, key)
    except Exception as error:
        raise cli_exc.CLIDeleteError(PRETTY_ENTITY_NAME, key) from error


def _data_output_callback(value: Path | None) -> Path | None:
    if value is not None:
        _, ext = os.path.splitext(value.name)
        if ext.lower() not in (".jsonl", ".csv"):
            raise typer.BadParameter(
                "Supported file extensions are '.jsonl' and '.csv'."
            )
    return value


@dataset_app.command("export")
def _export(
    key: str = cli_args.export_key_argument(PRETTY_ENTITY_NAME),
    output: Path | None = cli_args.export_output_path_option,
    data_output: Path | None = typer.Option(
        None,
        "-do",
        "--data-output",
        help=(
            "Path to output JSONL or CSV file (determined from the extension). "
            "Omit to print the first 10 samples to stdout."
        ),
        callback=_data_output_callback,
    ),
) -> None:
    """Export the dataset with the provided key (including the data contents)
    to a file or print as JSON."""
    if not output:
        cli_print.suppress_logging()

    client = get_client_from_env()
    try:
        stored_dataset = client.datasets.get_dataset_by_key(key)
        _assert_dataset_metadata_is_present(stored_dataset, output)
    except Exception as error:
        raise cli_exc.CLIExportError(PRETTY_ENTITY_NAME, key) from error

    try:
        jsonl_data = download_jsonl_data_from_client(
            # NOTE: We can safely cast as we asserted above
            client,
            cast(DatasetMetadata, stored_dataset.dataset_metadata).download_url,
        )
    except Exception as error:
        raise cli_exc.CLIDatasetDownloadError(key) from error

    try:
        cli_dataset = map_dataset_api_to_cli_entity(
            stored_dataset=stored_dataset,
            data_output=data_output,
            models_map=EntityByIdentifiersMap(client.models.get_models().models),
            datasets_map=EntityByIdentifiersMap(
                client.datasets.get_datasets().datasets
            ),
            dataset_generators_map=EntityByIdentifiersMap(
                client.dataset_generators.get_dataset_generators().dataset_generators
            ),
        )
    except Exception as error:
        raise cli_exc.CLIExportError(PRETTY_ENTITY_NAME, key) from error

    if data_output:
        try:
            save_jsonl_data_as_csv_or_jsonl(data_output, jsonl_data)
        except Exception as error:
            raise cli_exc.CLIDatasetSaveError(key) from error
    else:
        try:
            column_names, samples = parse_jsonl(jsonl_data, max_num_rows=10)
            cli_print.print_table(
                "Dataset samples preview",
                rows=samples,
                columns=[
                    (column_name, itemgetter(i))
                    for i, column_name in enumerate(column_names)
                ],
            )
        except Exception as error:
            raise cli_exc.CLIExportError(PRETTY_ENTITY_NAME, key) from error

    try:
        if output:
            dump_entity_to_yaml_file(output, cli_dataset)
            cli_print.log_export_success_info(PRETTY_ENTITY_NAME, output, key)
        else:
            cli_print.print_entities_as_json(cli_dataset)
    except Exception as error:
        raise cli_exc.CLIExportError(PRETTY_ENTITY_NAME, key) from error


@dataset_app.command("generation-preview")
def _generation_preview(
    path: Path = cli_args.single_config_path_argument(PRETTY_ENTITY_NAME),
    num_samples: int = typer.Option(
        3, help="The number of samples to generate. Can be at most 10."
    ),
) -> None:
    """Generate a preview (a few samples) of a dataset using the dataset generator
    specified in the YAML file."""
    if not path.is_file():
        raise cli_exc.CLIInvalidSingleFilePathError(path)

    client = get_client_from_env(read_timeout=60.0)
    try:
        cli_dataset, origin_info = _get_cli_dataset_from_file(path)
        _, _, dataset_generation_request_with_id = map_dataset_cli_to_api_entity(
            cli_dataset=cli_dataset,
            models_map=EntityByIdentifiersMap(client.models.get_models().models),
            datasets_map=EntityByIdentifiersMap(
                client.datasets.get_datasets().datasets
            ),
            dataset_generators_map=EntityByIdentifiersMap(
                client.dataset_generators.get_dataset_generators().dataset_generators
            ),
            origin_info=origin_info,
        )
    except Exception as error:
        raise cli_exc.CLIGenerateDatasetPreviewFromPathError(path) from error

    if not dataset_generation_request_with_id:
        raise cli_exc.CLIGenerateDatasetPreviewFromPathError(
            path,
            "Dataset generation requires the config to have a "
            "`dataset_generation_request` section.",
        )

    try:
        dataset_generation_request, dataset_generator_id = (
            dataset_generation_request_with_id
        )
        dataset_generation_request.num_samples = num_samples
        preview_data = client.dataset_generators.preview_dataset_generation(
            dataset_generator_id, dataset_generation_request
        )
        cli_print.print_table(
            "Generated dataset preview",
            preview_data.sample_rows,
            [
                (column_name, itemgetter(column_name))
                for column_name in preview_data.column_names
            ],
        )
    except Exception as error:
        raise cli_exc.CLIGenerateDatasetPreviewFromPathError(path) from error


def _get_cli_dataset_from_file(path: Path) -> tuple[CLICreateDataset, YAMLOriginInfo]:
    try:
        loaded_dict, origin_info = load_yaml_recursively(path)
        return CLICreateDataset.model_validate(
            loaded_dict, ignore_extra=False
        ), origin_info
    except Exception as error:
        raise cli_exc.CLIInvalidConfigError(
            PRETTY_ENTITY_NAME, path, "datasets"
        ) from error


def create_or_update_single_dataset(
    client: Client,
    dataset: Dataset,
    dataset_file_path: Path | None,
    dataset_generation_request_with_id: tuple[DatasetGenerationRequest, str] | None,
    stored_dataset: StoredDataset | None,
    verbosity: cli_print.Verbosity = "high",
) -> StoredDataset:
    if (
        stored_dataset
        and is_update_payload_same_as_existing_entity(dataset, stored_dataset)
        # NOTE: If the user is updating and providing a file path, we have no way of
        # telling if the dataset should be updated or not, so we always update. This
        # means we do not update iff `file_path is None`.
        and dataset_file_path is None
    ):
        cli_print.log_no_change_info(
            PRETTY_ENTITY_NAME, dataset.key, verbosity=verbosity
        )
        return stored_dataset
    elif stored_dataset:
        return _update_single_dataset(
            client=client,
            dataset=dataset,
            file_path=dataset_file_path,
            dataset_generation_request_with_id=dataset_generation_request_with_id,
            stored_dataset=stored_dataset,
            verbosity=verbosity,
        )
    else:
        return _create_single_dataset(
            client=client,
            dataset=dataset,
            file_path=dataset_file_path,
            dataset_generation_request_with_id=dataset_generation_request_with_id,
            verbosity=verbosity,
        )


def _create_single_dataset(
    client: Client,
    dataset: Dataset,
    file_path: Path | None,
    dataset_generation_request_with_id: tuple[DatasetGenerationRequest, str] | None,
    verbosity: cli_print.Verbosity,
) -> StoredDataset:
    cli_print.log_create_attempt_info(
        PRETTY_ENTITY_NAME, dataset.key, verbosity=verbosity
    )
    if file_path and not dataset_generation_request_with_id:
        stored_dataset = client.datasets.create_dataset_from_path(dataset, file_path)
    elif dataset_generation_request_with_id and not file_path:
        dataset_generation_request, dataset_generator_id = (
            dataset_generation_request_with_id
        )
        stored_dataset = client.dataset_generators.generate_dataset(
            dataset_generator_id,
            GeneratedDataset(
                display_name=dataset.display_name,
                description=dataset.description,
                key=dataset.key,
                dataset_generation_request=dataset_generation_request,
            ),
        )
    else:
        raise cli_exc.CLIError(
            "A dataset config must contain either `file_path`"
            " or `dataset_generation_request` but not both."
        )

    cli_print.log_create_success_info(
        PRETTY_ENTITY_NAME, stored_dataset.key, verbosity=verbosity
    )
    return stored_dataset


def _update_single_dataset(
    client: Client,
    dataset: Dataset,
    file_path: Path | None,
    dataset_generation_request_with_id: tuple[DatasetGenerationRequest, str] | None,
    stored_dataset: StoredDataset,
    verbosity: cli_print.Verbosity,
) -> StoredDataset:
    cli_print.log_update_attempt_info(
        PRETTY_ENTITY_NAME, stored_dataset.key, verbosity=verbosity
    )
    if dataset_generation_request_with_id:
        raise cli_exc.CLIUpdateError(
            PRETTY_ENTITY_NAME,
            stored_dataset.key,
            additional_message="Updating a dataset by generating new data is not supported.",
        )
    stored_dataset = client.datasets.update_dataset(stored_dataset.id, dataset)
    if file_path:
        stored_dataset = client.datasets.update_dataset_data_from_path(
            stored_dataset.id, file_path
        )
    cli_print.log_update_success_info(
        PRETTY_ENTITY_NAME, stored_dataset.key, verbosity=verbosity
    )
    return stored_dataset


def _assert_dataset_metadata_is_present(
    stored_dataset: StoredDataset, output_path: Path | None
) -> None:
    if stored_dataset.dataset_metadata:
        return

    # Unclear why the dataset is incomplete (shouldn't happen); use generic message.
    if stored_dataset.dataset_generation_metadata is None:
        raise cli_exc.CLIExportError(
            PRETTY_ENTITY_NAME,
            stored_dataset.key,
            output_path=output_path,
            additional_message="Dataset is incomplete.",
        )

    status = stored_dataset.dataset_generation_metadata.execution_status
    progress = stored_dataset.dataset_generation_metadata.progress
    if status == ExecutionStatus.FINISHED:
        # We include FINISHED here, because if the job finished but the dataset
        # still does not have any data, something went wrong.
        raise cli_exc.CLIExportError(
            PRETTY_ENTITY_NAME,
            stored_dataset.key,
            output_path=output_path,
            additional_message="Dataset generation failed.",
        )
    elif status in (ExecutionStatus.NOT_STARTED, ExecutionStatus.PENDING):
        if progress is None:
            raise cli_exc.CLIExportError(
                PRETTY_ENTITY_NAME,
                stored_dataset.key,
                output_path=output_path,
                additional_message="Dataset generation is in progress.",
            )
        raise cli_exc.CLIExportError(
            PRETTY_ENTITY_NAME,
            stored_dataset.key,
            output_path=output_path,
            additional_message=(
                "Dataset generation is in progress. "
                f"({100 * progress.progress:.1f}% complete.)"
            ),
        )


def _validate_datasets(config_files: list[Path]) -> None:
    for config_file in config_files:
        try:
            _get_cli_dataset_from_file(config_file)
            cli_print.log_validation_success_info(config_file)
        except Exception as error:
            raise cli_exc.CLIValidationError(PRETTY_ENTITY_NAME) from error
