from __future__ import annotations

import copy
from pathlib import Path
from typing import Any
from typing import cast
from typing import Generic
from typing import List
from typing import Protocol
from typing import TypeVar

from latticeflow.go.cli.utils.dtypes import CLICreateAIApp
from latticeflow.go.cli.utils.dtypes import CLICreateDataset
from latticeflow.go.cli.utils.dtypes import CLICreateDatasetGenerator
from latticeflow.go.cli.utils.dtypes import CLICreateEvaluation
from latticeflow.go.cli.utils.dtypes import CLICreateModel
from latticeflow.go.cli.utils.dtypes import CLICreateModelAdapter
from latticeflow.go.cli.utils.dtypes import CLICreateTask
from latticeflow.go.cli.utils.dtypes import CLIDatasetGeneratorSpecification
from latticeflow.go.cli.utils.dtypes import (
    CLIDeclarativeDatasetGeneratorDefinitionTemplate,
)
from latticeflow.go.cli.utils.dtypes import CLIDeclarativeTaskDefinitionTemplate
from latticeflow.go.cli.utils.dtypes import CLIExportAIApp
from latticeflow.go.cli.utils.dtypes import CLIExportDataset
from latticeflow.go.cli.utils.dtypes import CLIExportDatasetGenerator
from latticeflow.go.cli.utils.dtypes import CLIExportModel
from latticeflow.go.cli.utils.dtypes import CLIExportModelAdapter
from latticeflow.go.cli.utils.dtypes import CLIExportTask
from latticeflow.go.cli.utils.dtypes import CLIPredefinedTaskDefinition
from latticeflow.go.cli.utils.dtypes import CLITaskDatasetTemplate
from latticeflow.go.cli.utils.dtypes import ConfigSpecType
from latticeflow.go.cli.utils.dtypes import ParameterSpecType
from latticeflow.go.cli.utils.dtypes import UserOrLFKey
from latticeflow.go.cli.utils.exceptions import CLIEntityMappingError
from latticeflow.go.cli.utils.exceptions import CLIError
from latticeflow.go.models import AIApp
from latticeflow.go.models import AIAppKeyInformation
from latticeflow.go.models import Dataset
from latticeflow.go.models import DatasetGenerationRequest
from latticeflow.go.models import DatasetGenerator
from latticeflow.go.models import DatasetGeneratorDataSourceTemplate
from latticeflow.go.models import DatasetGeneratorSynthesizerTemplate
from latticeflow.go.models import DeclarativeDatasetGeneratorDefinitionTemplate
from latticeflow.go.models import DeclarativeTaskDefinitionTemplate
from latticeflow.go.models import EvaluatedEntityType
from latticeflow.go.models import Evaluation
from latticeflow.go.models import EvaluationConfig
from latticeflow.go.models import Model
from latticeflow.go.models import ModelAdapter
from latticeflow.go.models import PredefinedTaskDefinition
from latticeflow.go.models import StoredAIApp
from latticeflow.go.models import StoredDataset
from latticeflow.go.models import StoredDatasetGenerator
from latticeflow.go.models import StoredModel
from latticeflow.go.models import StoredModelAdapter
from latticeflow.go.models import StoredTask
from latticeflow.go.models import Task
from latticeflow.go.models import TaskDatasetTemplate
from latticeflow.go.models import TaskScorerTemplate
from latticeflow.go.models import TaskSpecification
from latticeflow.go.utils.resolution import YAMLOriginInfo


####################################################################################
# MAPPING:
#
# These functions are used to map CLI entities to API entities and API entities to
# CLI entities. The CLI entities are loaded from YAML files provided by the user
# when creating an entity using the CLI, and the API entities are loaded from the
# API when exporting an entity from AI GO! using the CLI.
#
# Couple of gotchas
# - for user-specified references (specified in configs such as the dataset
#   generator config) we assume the user-specified value is always a key, and that
#   the schema of the YAML conforms to the structure of the Pydantic CLI models.
# - for dynamic placeholders in the config specification (e.g. `<<foo>>`) we skip
#   any replacment logic, as the value will later be correctly replaced by the
#   mapping functions when the payload to the config will be sent.
# - all of the mapping functions below create and return a mapped copy, never
#   modifying the original provided dictionary or object.
####################################################################################


class HasId(Protocol):
    id: str


class HasKey(Protocol):
    key: str


class HasKeyAndId(HasId, HasKey, Protocol):
    pass


T = TypeVar("T", bound=HasKeyAndId)


class EntityByIdentifiersMap(Generic[T]):
    def __init__(self, entities: list[T]) -> None:
        self.entity_map_by_key = {entity.key: entity for entity in entities}
        self.entity_map_by_id = {entity.id: entity for entity in entities}

    def get_entity_by_id(self, searched_id: str) -> T | None:
        return self.entity_map_by_id.get(searched_id)

    def get_entity_by_key(self, searched_key: str) -> T | None:
        return self.entity_map_by_key.get(searched_key)

    def get_key_by_id(self, searched_id: str) -> str | None:
        entity = self.get_entity_by_id(searched_id)
        return entity.key if entity else None

    def get_id_by_key(self, searched_key: str) -> str | None:
        entity = self.get_entity_by_key(searched_key)
        return entity.id if entity else None

    def update_entity(self, entity: T) -> None:
        self.entity_map_by_key[entity.key] = entity
        self.entity_map_by_id[entity.id] = entity


def is_dynamic_placeholder(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    stripped_value = value.strip()
    return stripped_value.startswith("<<") and stripped_value.endswith(">>")


def map_config_keys_to_ids(
    *,
    config_dict: dict,
    config_spec: ConfigSpecType,
    models_map: EntityByIdentifiersMap[StoredModel],
    datasets_map: EntityByIdentifiersMap[StoredDataset],
    config_file: Path,
) -> dict:
    """Replace model and dataset keys in a configuration dictionary with their
    corresponding IDs.

    This function iterates over the entries in the provided configuration dictionary and, based on
    the configuration specification, replaces values that refer to models or datasets by key with
    their respective IDs. It uses the provided entity maps to resolve the key-ID mappings. Dynamic
    placeholders are skipped.

    Args:
        config_dict: Configuration dictionary potentially containing model or dataset keys.
        config_spec: Specification defining which configuration parameters refer to which parameter type.
        models_map: Mapping between model IDs and keys.
        datasets_map: Mapping between dataset IDs and keys.
        config_file: Path to the YAML configuration file, used for error reporting.

    Returns:
        A deep-copied configuration dictionary with all model and dataset keys replaced by their IDs.

    Raises:
        CLIError: If a referenced model or dataset key does not exist in the respective entity map.
    """
    config_dict_copy = copy.deepcopy(config_dict)
    for config_dictionary_key, config_value in config_dict_copy.items():
        if is_dynamic_placeholder(config_value):
            continue
        matching_parameter_spec = _get_matching_parameter_spec(
            config_spec, config_dictionary_key
        )
        if not matching_parameter_spec:
            continue

        if matching_parameter_spec.type == "model":
            if matching_model_id := models_map.get_id_by_key(config_value):
                config_dict_copy[config_dictionary_key] = matching_model_id
            else:
                raise CLIError(
                    f"No model with key '{config_value}' exists (specified using "
                    f"property key '{config_dictionary_key}'). File: '{config_file}'."
                )
        elif matching_parameter_spec.type == "dataset":
            if matching_dataset_id := datasets_map.get_id_by_key(config_value):
                config_dict_copy[config_dictionary_key] = matching_dataset_id
            else:
                raise CLIError(
                    f"No dataset with key '{config_value}' exists (specified using "
                    f"property key '{config_dictionary_key}'). File: '{config_file}'."
                )

    return config_dict_copy


def map_config_ids_to_keys(
    *,
    config_dict: dict,
    config_spec: ConfigSpecType,
    models_map: EntityByIdentifiersMap[StoredModel],
    datasets_map: EntityByIdentifiersMap[StoredDataset],
) -> dict:
    """Replace model and dataset IDs in a configuration dictionary with their
    corresponding keys.

    This function iterates through the configuration dictionary and replaces IDs with their
    readable keys according to the given configuration specification. Dynamic placeholders
    are skipped.

    Args:
        config_dict: Configuration dictionary potentially containing model or dataset IDs.
        config_spec: Specification defining which configuration parameters refer to which entity type.
        models_map: Mapping between model IDs and keys.
        datasets_map: Mapping between dataset IDs and keys.

    Returns:
        A deep-copied configuration dictionary with all model and dataset IDs replaced by their keys.

    Raises:
        CLIError: If a referenced model or dataset ID does not exist in the respective entity map.
    """
    config_dict_copy = copy.deepcopy(config_dict)
    for config_dictionary_key, config_value in config_dict_copy.items():
        if is_dynamic_placeholder(config_value):
            continue
        matching_parameter_spec = _get_matching_parameter_spec(
            config_spec, config_dictionary_key
        )
        if not matching_parameter_spec:
            continue

        if matching_parameter_spec.type == "model":
            if matching_model_key := models_map.get_key_by_id(config_value):
                config_dict_copy[config_dictionary_key] = matching_model_key
            else:
                raise CLIError(
                    f"No model with ID '{config_value}' exists (specified using "
                    f"property key '{config_dictionary_key}')."
                )
        elif matching_parameter_spec.type == "dataset":
            if dataset_key := datasets_map.get_key_by_id(config_value):
                config_dict_copy[config_dictionary_key] = dataset_key
            else:
                raise CLIError(
                    f"No dataset with id '{config_value}' exists (specified using "
                    f"property key '{config_dictionary_key}')."
                )

    return config_dict_copy


def _get_matching_parameter_spec(
    config_spec: ConfigSpecType, config_dictionary_key: str
) -> ParameterSpecType | None:
    return next(
        (
            parameter_spec
            for parameter_spec in config_spec
            if parameter_spec.key == config_dictionary_key
        ),
        None,
    )


def map_ai_app_cli_to_api_entity(
    *, cli_ai_app: CLICreateAIApp, config_file: Path
) -> AIApp:
    try:
        return AIApp(
            display_name=cli_ai_app.display_name,
            key=cli_ai_app.key,
            description=cli_ai_app.description,
            long_description=cli_ai_app.long_description,
            key_info=cli_ai_app.key_info
            if cli_ai_app.key_info
            else AIAppKeyInformation(),
            industry_type=cli_ai_app.industry_type,
        )
    except Exception as error:
        raise CLIEntityMappingError("AI app", config_file) from error


def map_ai_app_api_to_cli_entity(*, stored_ai_app: StoredAIApp) -> CLIExportAIApp:
    try:
        return CLIExportAIApp(
            display_name=stored_ai_app.display_name,
            key=stored_ai_app.key,
            description=stored_ai_app.description,
            long_description=stored_ai_app.long_description,
            key_info=stored_ai_app.key_info,
            industry_type=stored_ai_app.industry_type,
        )
    except Exception as error:
        raise CLIEntityMappingError("AI app", None) from error


def map_dataset_generator_cli_to_api_entity(
    *,
    cli_dataset_generator: CLICreateDatasetGenerator,
    datasets_map: EntityByIdentifiersMap[StoredDataset],
    models_map: EntityByIdentifiersMap[StoredModel],
    config_file: Path,
) -> DatasetGenerator:
    try:
        definition = DeclarativeDatasetGeneratorDefinitionTemplate(
            type="declarative_dataset_generator",
            data_source=_map_dataset_data_source_config_from_keys_to_ids(
                data_source=cli_dataset_generator.definition.data_source,
                datasets_map=datasets_map,
                config_file=config_file,
            ),
            synthesizer=_map_dataset_synthesizer_config_from_keys_to_ids(
                synthesizer=cli_dataset_generator.definition.synthesizer,
                models_map=models_map,
                config_file=config_file,
            ),
        )

        return DatasetGenerator(
            key=cli_dataset_generator.key,
            display_name=cli_dataset_generator.display_name,
            description=cli_dataset_generator.description,
            long_description=cli_dataset_generator.long_description,
            config_spec=cli_dataset_generator.config_spec,
            definition=definition,
            tags=cli_dataset_generator.tags,
        )
    except Exception as error:
        raise CLIEntityMappingError("dataset generator", config_file) from error


def _map_dataset_data_source_config_from_keys_to_ids(
    *,
    data_source: DatasetGeneratorDataSourceTemplate,
    datasets_map: EntityByIdentifiersMap[StoredDataset],
    config_file: Path,
) -> DatasetGeneratorDataSourceTemplate:
    data_source_dict = data_source.model_dump()
    if data_source_dataset_key := data_source_dict.pop("dataset_key", None):
        if is_dynamic_placeholder(data_source_dataset_key):
            data_source_dataset_id = data_source_dataset_key
        elif not (
            data_source_dataset_id := datasets_map.get_id_by_key(
                data_source_dataset_key
            )
        ):
            raise CLIError(
                f"No dataset with key '{data_source_dataset_key}' exists. File: '{config_file}'."
            )
        data_source_dict["dataset_id"] = data_source_dataset_id
    if data_source_dataset_keys := data_source_dict.pop("dataset_keys", None):
        if not isinstance(data_source_dataset_keys, list):
            raise CLIError(f"'dataset_keys' must be a list. File: '{config_file}'.")
        data_source_dataset_ids = []
        for data_source_dataset_key in data_source_dataset_keys:
            if is_dynamic_placeholder(data_source_dataset_key):
                data_source_dataset_id = data_source_dataset_key
            elif not (
                data_source_dataset_id := datasets_map.get_id_by_key(
                    data_source_dataset_key
                )
            ):
                raise CLIError(
                    f"No dataset with key '{data_source_dataset_key}' exists. File: '{config_file}'."
                )
            data_source_dataset_ids.append(data_source_dataset_id)
        data_source_dict["dataset_ids"] = data_source_dataset_ids
    return DatasetGeneratorDataSourceTemplate.model_validate(data_source_dict)


def _map_dataset_synthesizer_config_from_keys_to_ids(
    *,
    synthesizer: DatasetGeneratorSynthesizerTemplate,
    models_map: EntityByIdentifiersMap[StoredModel],
    config_file: Path,
) -> DatasetGeneratorSynthesizerTemplate:
    synthesizer_dict = synthesizer.model_dump()
    if synthesizer_model_key := synthesizer_dict.pop("model_key", None):
        if is_dynamic_placeholder(synthesizer_model_key):
            synthesizer_model_id = synthesizer_model_key
        elif not (
            synthesizer_model_id := models_map.get_id_by_key(synthesizer_model_key)
        ):
            raise CLIError(
                f"No model with key '{synthesizer_model_key}' exists. File: '{config_file}'."
            )
        synthesizer_dict["model_id"] = synthesizer_model_id
    return DatasetGeneratorSynthesizerTemplate.model_validate(synthesizer_dict)


def map_dataset_generator_api_to_cli_entity(
    *,
    stored_dataset_generator: StoredDatasetGenerator,
    datasets_map: EntityByIdentifiersMap[StoredDataset],
    models_map: EntityByIdentifiersMap[StoredModel],
) -> CLIExportDatasetGenerator:
    try:
        definition = CLIDeclarativeDatasetGeneratorDefinitionTemplate(
            type="declarative_dataset_generator",
            data_source=_map_dataset_data_source_config_from_ids_to_keys(
                data_source=stored_dataset_generator.definition.data_source,
                datasets_map=datasets_map,
            ),
            synthesizer=_map_dataset_synthesizer_config_from_ids_to_keys(
                synthesizer=stored_dataset_generator.definition.synthesizer,
                models_map=models_map,
            ),
        )

        return CLIExportDatasetGenerator(
            key=stored_dataset_generator.key,
            display_name=stored_dataset_generator.display_name,
            description=stored_dataset_generator.description,
            long_description=stored_dataset_generator.long_description,
            config_spec=stored_dataset_generator.config_spec,
            definition=definition,
            tags=stored_dataset_generator.tags,
        )
    except Exception as error:
        raise CLIEntityMappingError("dataset generator", None) from error


def _map_dataset_data_source_config_from_ids_to_keys(
    *,
    data_source: DatasetGeneratorDataSourceTemplate,
    datasets_map: EntityByIdentifiersMap[StoredDataset],
) -> DatasetGeneratorDataSourceTemplate:
    data_source_dict = data_source.model_dump()
    if dataset_generator_source_dataset_id := data_source_dict.pop("dataset_id", None):
        if is_dynamic_placeholder(dataset_generator_source_dataset_id):
            dataset_generator_source_dataset_key = dataset_generator_source_dataset_id
        else:
            # This has just come from the API, so we assume it exists.
            dataset_generator_source_dataset_key = cast(
                str, datasets_map.get_key_by_id(dataset_generator_source_dataset_id)
            )
        data_source_dict["dataset_key"] = dataset_generator_source_dataset_key
    return DatasetGeneratorDataSourceTemplate.model_validate(data_source_dict)


def _map_dataset_synthesizer_config_from_ids_to_keys(
    *,
    synthesizer: DatasetGeneratorSynthesizerTemplate,
    models_map: EntityByIdentifiersMap[StoredModel],
) -> DatasetGeneratorSynthesizerTemplate:
    synthesizer_dict = synthesizer.model_dump()
    if dataset_generator_synthesizer_model_id := synthesizer_dict.pop("model_id", None):
        if is_dynamic_placeholder(dataset_generator_synthesizer_model_id):
            dataset_generator_synthesizer_model_key = (
                dataset_generator_synthesizer_model_id
            )
        else:
            # This has just come from the API, so we assume it exists.
            dataset_generator_synthesizer_model_key = cast(
                str, models_map.get_key_by_id(dataset_generator_synthesizer_model_id)
            )
        synthesizer_dict["model_key"] = dataset_generator_synthesizer_model_key
    return DatasetGeneratorSynthesizerTemplate.model_validate(synthesizer_dict)


def map_model_cli_to_api_entity(
    *,
    cli_model: CLICreateModel,
    model_adapters_map: EntityByIdentifiersMap[StoredModelAdapter],
    config_file: Path,
) -> Model:
    try:
        if not (
            matching_model_adapter_id := model_adapters_map.get_id_by_key(
                cli_model.adapter.key
            )
        ):
            raise CLIError(
                f"No model adapter with key '{cli_model.adapter.key}' exists."
                f" File: '{config_file}'."
            )

        return Model(
            display_name=cli_model.display_name,
            key=cli_model.key,
            description=cli_model.description,
            rate_limit=cli_model.rate_limit,
            modality=cli_model.modality,
            task=cli_model.task,
            adapter_id=matching_model_adapter_id,
            config=cli_model.config,
        )
    except Exception as error:
        raise CLIEntityMappingError("model", config_file) from error


def map_model_api_to_cli_entity(
    *,
    stored_model: StoredModel,
    model_adapters_map: EntityByIdentifiersMap[StoredModelAdapter],
) -> CLIExportModel:
    try:
        return CLIExportModel(
            key=stored_model.key,
            display_name=stored_model.display_name,
            description=stored_model.description,
            rate_limit=stored_model.rate_limit,
            modality=stored_model.modality,
            task=stored_model.task,
            adapter=UserOrLFKey(
                # This has just come from the API, so we assume it exists.
                key=cast(str, model_adapters_map.get_key_by_id(stored_model.adapter_id))
            ),
            config=stored_model.config,
        )
    except Exception as error:
        raise CLIEntityMappingError("model", None) from error


def map_model_adapter_cli_to_api_entity(
    *, cli_model_adapter: CLICreateModelAdapter, config_file: Path
) -> ModelAdapter:
    try:
        return ModelAdapter(
            display_name=cli_model_adapter.display_name,
            description=cli_model_adapter.description,
            long_description=cli_model_adapter.long_description,
            key=cli_model_adapter.key,
            provider=cli_model_adapter.provider,
            modality=cli_model_adapter.modality,
            task=cli_model_adapter.task,
            process_input=cli_model_adapter.process_input,
            process_output=cli_model_adapter.process_output,
        )
    except Exception as error:
        raise CLIEntityMappingError("model adapter", config_file) from error


def map_model_adapter_api_to_cli_entity(
    *, stored_model_adapter: StoredModelAdapter
) -> CLIExportModelAdapter:
    try:
        return CLIExportModelAdapter(
            display_name=stored_model_adapter.display_name,
            description=stored_model_adapter.description,
            long_description=stored_model_adapter.long_description,
            key=stored_model_adapter.key,
            provider=stored_model_adapter.provider,
            modality=stored_model_adapter.modality,
            task=stored_model_adapter.task,
            process_input=stored_model_adapter.process_input,
            process_output=stored_model_adapter.process_output,
        )
    except Exception as error:
        raise CLIEntityMappingError("model adapter", None) from error


def map_dataset_cli_to_api_entity(
    *,
    cli_dataset: CLICreateDataset,
    models_map: EntityByIdentifiersMap[StoredModel],
    datasets_map: EntityByIdentifiersMap[StoredDataset],
    dataset_generators_map: EntityByIdentifiersMap[StoredDatasetGenerator],
    origin_info: YAMLOriginInfo,
) -> tuple[Dataset, Path | None, tuple[DatasetGenerationRequest, str] | None]:
    try:
        dataset_generation_request_with_id: (
            tuple[DatasetGenerationRequest, str] | None
        ) = None
        if cli_dataset.generator_specification:
            dataset_generator_key = (
                cli_dataset.generator_specification.dataset_generator_key
            )
            if not (
                matching_dataset_generator := dataset_generators_map.get_entity_by_key(
                    dataset_generator_key
                )
            ):
                raise CLIError(
                    f"No dataset generator with key '{dataset_generator_key}' exists. "
                    f"File: '{origin_info.get_root_file_path()}'."
                )
            dataset_generation_request_with_id = (
                DatasetGenerationRequest(
                    dataset_generator_config=map_config_keys_to_ids(
                        config_dict=cli_dataset.generator_specification.dataset_generator_config,
                        config_spec=matching_dataset_generator.config_spec,
                        models_map=models_map,
                        datasets_map=datasets_map,
                        config_file=origin_info.get_root_file_path(),
                    ),
                    num_samples=cli_dataset.generator_specification.num_samples,
                ),
                matching_dataset_generator.id,
            )

        if cli_dataset.file_path is None:
            file_path = None
        else:
            file_path = cli_dataset.file_path
            if not file_path.is_absolute():
                base_path = origin_info.get("file_path").get_file_path().parent
                file_path = (base_path / file_path).resolve(strict=False)
        return (
            Dataset(
                display_name=cli_dataset.display_name,
                description=cli_dataset.description,
                key=cli_dataset.key,
            ),
            file_path,
            dataset_generation_request_with_id,
        )
    except Exception as error:
        raise CLIEntityMappingError(
            "dataset", origin_info.get_root_file_path()
        ) from error


def map_dataset_api_to_cli_entity(
    *,
    stored_dataset: StoredDataset,
    data_output: Path | None,
    models_map: EntityByIdentifiersMap[StoredModel],
    datasets_map: EntityByIdentifiersMap[StoredDataset],
    dataset_generators_map: EntityByIdentifiersMap[StoredDatasetGenerator],
) -> CLIExportDataset:
    try:
        cli_generator_specification: CLIDatasetGeneratorSpecification | None = None
        if stored_dataset.dataset_generation_metadata:
            # This has just come from the API, so we assume it exists.
            matching_dataset_generator = cast(
                StoredDatasetGenerator,
                dataset_generators_map.get_entity_by_id(
                    stored_dataset.dataset_generation_metadata.dataset_generator_id
                ),
            )
            cli_generator_specification = CLIDatasetGeneratorSpecification(
                dataset_generator_config=map_config_ids_to_keys(
                    config_dict=stored_dataset.dataset_generation_metadata.dataset_generation_request.dataset_generator_config,
                    config_spec=matching_dataset_generator.config_spec,
                    models_map=models_map,
                    datasets_map=datasets_map,
                ),
                num_samples=stored_dataset.dataset_generation_metadata.dataset_generation_request.num_samples,
                dataset_generator_key=matching_dataset_generator.key,
            )

        return CLIExportDataset(
            display_name=stored_dataset.display_name,
            description=stored_dataset.description,
            key=stored_dataset.key,
            file_path=data_output.absolute() if data_output else None,
            generator_specification=cli_generator_specification,
        )
    except Exception as error:
        raise CLIEntityMappingError("dataset", None) from error


def map_task_cli_to_api_entity(
    *,
    cli_task: CLICreateTask,
    datasets_map: EntityByIdentifiersMap[StoredDataset],
    models_map: EntityByIdentifiersMap[StoredModel],
    config_file: Path,
) -> Task:
    try:
        if isinstance(cli_task.definition, CLIDeclarativeTaskDefinitionTemplate):
            dataset_key = cli_task.definition.dataset.key
            if is_dynamic_placeholder(dataset_key):
                dataset_source_id = dataset_key
            else:
                if not (
                    optional_dataset_source_id := datasets_map.get_id_by_key(
                        dataset_key
                    )
                ):
                    raise CLIError(
                        f"No dataset with key '{dataset_key}' exists. File: '{config_file}'."
                    )
                dataset_source_id = optional_dataset_source_id

            definition: DeclarativeTaskDefinitionTemplate | PredefinedTaskDefinition = (
                DeclarativeTaskDefinitionTemplate(
                    type="declarative_task",
                    dataset=TaskDatasetTemplate(
                        id=dataset_source_id,
                        fast_subset_size=cli_task.definition.dataset.fast_subset_size,
                    ),
                    solver=cli_task.definition.solver,
                    scorers=_map_declarative_task_scorers_from_keys_to_ids(
                        scorers=cli_task.definition.scorers,
                        models_map=models_map,
                        config_file=config_file,
                    ),
                )
            )
        else:
            definition = PredefinedTaskDefinition(type="predefined")

        return Task(
            key=cli_task.key,
            display_name=cli_task.display_name,
            description=cli_task.description,
            long_description=cli_task.long_description,
            tags=cli_task.tags,
            modalities=cli_task.modalities,
            tasks=cli_task.tasks,
            evaluated_entity_type=cli_task.evaluated_entity_type,
            config_spec=cli_task.config_spec,
            definition=definition,
        )
    except Exception as error:
        raise CLIEntityMappingError("task", config_file) from error


def _map_declarative_task_scorers_from_keys_to_ids(
    *,
    scorers: List[TaskScorerTemplate],
    models_map: EntityByIdentifiersMap[StoredModel],
    config_file: Path,
) -> List[TaskScorerTemplate]:
    mapped_scorers: list[TaskScorerTemplate] = []
    for scorer in scorers:
        scorer_dict = scorer.model_dump()
        scorer_model_id_name: str | None = None
        if scorer_model_key := scorer_dict.pop("model_key", None):
            scorer_model_id_name = "model_id"
        elif scorer_model_key := scorer_dict.pop("judge_model_key", None):
            scorer_model_id_name = "judge_model_id"

        if scorer_model_key and scorer_model_id_name:
            if is_dynamic_placeholder(scorer_model_key):
                scorer_model_id = scorer_model_key
            elif not (scorer_model_id := models_map.get_id_by_key(scorer_model_key)):
                raise CLIError(
                    f"No model with key '{scorer_model_key}' exists. File: '{config_file}'."
                )
            scorer_dict[scorer_model_id_name] = scorer_model_id
        mapped_scorers.append(TaskScorerTemplate.model_validate(scorer_dict))

    return mapped_scorers


def map_task_api_to_cli_entity(
    *,
    stored_task: StoredTask,
    models_map: EntityByIdentifiersMap[StoredModel],
    datasets_map: EntityByIdentifiersMap[StoredDataset],
) -> CLIExportTask:
    try:
        if isinstance(stored_task.definition, DeclarativeTaskDefinitionTemplate):
            task_dataset_id = stored_task.definition.dataset.id
            if is_dynamic_placeholder(task_dataset_id):
                task_dataset_key: str = task_dataset_id
            else:
                # This has just come from the API, so we assume it exists.
                task_dataset_key = cast(
                    str, datasets_map.get_key_by_id(task_dataset_id)
                )

            definition: (
                CLIDeclarativeTaskDefinitionTemplate | CLIPredefinedTaskDefinition
            ) = CLIDeclarativeTaskDefinitionTemplate(
                type="declarative_task",
                dataset=CLITaskDatasetTemplate(
                    key=task_dataset_key,
                    fast_subset_size=stored_task.definition.dataset.fast_subset_size,
                ),
                solver=stored_task.definition.solver,
                scorers=_map_declarative_task_scorers_from_ids_to_keys(
                    scorers=stored_task.definition.scorers, models_map=models_map
                ),
            )
        else:
            definition = CLIPredefinedTaskDefinition(type="predefined")

        return CLIExportTask(
            key=stored_task.key,
            display_name=stored_task.display_name,
            description=stored_task.description,
            long_description=stored_task.long_description,
            tags=stored_task.tags,
            modalities=stored_task.modalities,
            tasks=stored_task.tasks,
            evaluated_entity_type=stored_task.evaluated_entity_type,
            config_spec=stored_task.config_spec,
            definition=definition,
        )
    except Exception as error:
        raise CLIEntityMappingError("task", None) from error


def _map_declarative_task_scorers_from_ids_to_keys(
    *,
    scorers: List[TaskScorerTemplate],
    models_map: EntityByIdentifiersMap[StoredModel],
) -> List[TaskScorerTemplate]:
    mapped_scorers: list[TaskScorerTemplate] = []
    for scorer in scorers:
        scorer_dict = scorer.model_dump()
        scorer_model_key_name: str | None = None
        if scorer_model_id := scorer_dict.pop("model_id", None):
            scorer_model_key_name = "model_key"
        elif scorer_model_id := scorer_dict.pop("judge_model_id", None):
            scorer_model_key_name = "judge_model_key"

        if scorer_model_id and scorer_model_key_name:
            if is_dynamic_placeholder(scorer_model_id):
                scorer_model_key = scorer_model_id
            else:
                # This has just come from the API, so we assume it exists.
                scorer_model_key = cast(str, models_map.get_key_by_id(scorer_model_id))
            scorer_dict[scorer_model_key_name] = scorer_model_key
        mapped_scorers.append(TaskScorerTemplate.model_validate(scorer_dict))

    return mapped_scorers


def map_evaluation_cli_to_api_entity(
    *,
    cli_evaluation: CLICreateEvaluation,
    models_map: EntityByIdentifiersMap[StoredModel],
    datasets_map: EntityByIdentifiersMap[StoredDataset],
    tasks_map: EntityByIdentifiersMap[StoredTask],
    config_file: Path,
) -> Evaluation:
    try:
        task_specifications: list[TaskSpecification] = []
        for cli_task_specification in cli_evaluation.task_specifications:
            matching_task = tasks_map.get_entity_by_key(cli_task_specification.task_key)
            if not matching_task:
                raise CLIError(
                    f"No task with key '{cli_task_specification.task_key}' exists. File: '{config_file}'."
                )
            task_specifications.append(
                TaskSpecification(
                    task_id=matching_task.id,
                    task_config=map_config_keys_to_ids(
                        config_dict=cli_task_specification.task_config,
                        config_spec=matching_task.config_spec,
                        models_map=models_map,
                        datasets_map=datasets_map,
                        config_file=config_file,
                    ),
                    entity_id=_map_task_specification_model_key_to_entity_id(
                        model_key=cli_task_specification.model_key,
                        matching_task=matching_task,
                        models_map=models_map,
                        config_file=config_file,
                    )
                    if cli_task_specification.model_key
                    else None,
                    display_name=cli_task_specification.display_name,
                )
            )

        return Evaluation(
            display_name=cli_evaluation.display_name,
            key=cli_evaluation.key,
            task_specifications=task_specifications,
            config=EvaluationConfig(mode=cli_evaluation.mode),
        )
    except Exception as error:
        raise CLIEntityMappingError("evaluation", config_file) from error


def _map_task_specification_model_key_to_entity_id(
    *,
    model_key: str,
    matching_task: StoredTask,
    models_map: EntityByIdentifiersMap[StoredModel],
    config_file: Path,
) -> str:
    if matching_task.evaluated_entity_type == EvaluatedEntityType.MODEL:
        if not (matching_model_id := models_map.get_id_by_key(model_key)):
            raise CLIError(
                f"No entity (model) with key '{model_key}' exists. File: '{config_file}'."
            )
    else:
        raise CLIError(
            f"Only tasks that evaluate models are supported. File: '{config_file}'."
        )

    return matching_model_id
