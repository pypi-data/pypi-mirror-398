from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from latticeflow.go.cli.utils.dtypes import CLICreateDataset
from latticeflow.go.cli.utils.dtypes import CLICreateDatasetGenerator
from latticeflow.go.cli.utils.dtypes import CLICreateEvaluation
from latticeflow.go.cli.utils.dtypes import CLICreateModel
from latticeflow.go.cli.utils.dtypes import CLICreateModelAdapter
from latticeflow.go.cli.utils.dtypes import CLICreateProviderAndModelKey
from latticeflow.go.cli.utils.dtypes import CLICreateRunConfig
from latticeflow.go.cli.utils.dtypes import CLICreateTask
from latticeflow.go.cli.utils.exceptions import CLIError
from latticeflow.go.cli.utils.schema_mappers import EntityByIdentifiersMap
from latticeflow.go.models import StoredDatasetGenerator


CrossDependentEntities = CLICreateDataset | CLICreateDatasetGenerator

NodeId = tuple[Literal["dataset", "dataset generator"], str]


def _cross_entity_type_priority(node_id: tuple[str, str]) -> int:
    kind, _ = node_id
    return 0 if kind == "dataset generator" else 1


def _get_node_id(entity: CrossDependentEntities) -> NodeId:
    if isinstance(entity, CLICreateDataset):
        return ("dataset", entity.key)
    if isinstance(entity, CLICreateDatasetGenerator):
        return ("dataset generator", entity.key)


@dataclass(frozen=True)
class Dependency:
    depends_on: CrossDependentEntities
    dependent: CrossDependentEntities


def build_run_config_dependencies(
    *,
    cli_dataset_generators: list[CLICreateDatasetGenerator],
    cli_datasets: list[CLICreateDataset],
    dataset_generators_map: EntityByIdentifiersMap[StoredDatasetGenerator],
    config_file: Path,
) -> list[Dependency]:
    """Builds dependencies between dataset generators and datasets defined
    in the run config. No other entities can have _problematic_ dependencies,
    therefore we only resolve dependencies for those two entity types.

    The dependencies are guaranteed to:
    - not have duplicates
    - only include dependencies between entities defined in the run config
       (i.e. no external dependencies)
    """
    dependencies: list[Dependency] = []
    _build_dataset_generator_dependencies(
        dependencies=dependencies,
        cli_dataset_generators=cli_dataset_generators,
        cli_datasets=cli_datasets,
        config_file=config_file,
    )
    _build_dataset_dependencies(
        dependencies=dependencies,
        cli_dataset_generators=cli_dataset_generators,
        cli_datasets=cli_datasets,
        dataset_generators_map=dataset_generators_map,
    )
    _assert_no_duplicated_dependencies(
        dependencies=dependencies, config_file=config_file
    )
    return dependencies


def _assert_no_duplicated_dependencies(
    *, dependencies: list[Dependency], config_file: Path
) -> None:
    seen_dependencies: set[tuple[NodeId, NodeId]] = set()
    for dependency in dependencies:
        dependency_key = (
            _get_node_id(dependency.depends_on),
            _get_node_id(dependency.dependent),
        )
        if dependency_key in seen_dependencies:
            dependency_source_node_id, dependency_destination_node_id = dependency_key
            dependency_source_type, dependency_source_key = dependency_source_node_id
            dependency_destination_type, dependency_destination_key = (
                dependency_destination_node_id
            )
            raise CLIError(
                f"Duplicated dependency detected between {dependency_source_type}"
                f" with key '{dependency_source_key}' and {dependency_destination_type}"
                f" with key '{dependency_destination_key}'. File: '{config_file}'."
            )
        seen_dependencies.add(dependency_key)


def _build_dataset_generator_dependencies(
    *,
    dependencies: list[Dependency],
    cli_dataset_generators: list[CLICreateDatasetGenerator],
    cli_datasets: list[CLICreateDataset],
    config_file: Path,
) -> None:
    for cli_dataset_generator in cli_dataset_generators:
        data_source = cli_dataset_generator.definition.data_source
        # The `dataset_key` is only filled if a dataset generator has a hard-coded
        # dataset as data source. If it's dynamic (i.e. filled at runtime), then
        # it will be a placeholder string (e.g. `<<DYNAMIC_DATASET>>`) and will be later
        # filled through `dataset.generator_specification.dataset_generator_config`.
        if (dataset_key := getattr(data_source, "dataset_key", None)) is not None:
            if not isinstance(dataset_key, str):
                raise CLIError(
                    f"'dataset_key' must be a string. File: '{config_file}'."
                )
            # We check whether the referenced dataset exists in this run
            # config. If not, it's not a dependency we need to resolve here.
            matching_dataset_from_run_config = next(
                (
                    cli_dataset
                    for cli_dataset in cli_datasets
                    if dataset_key == cli_dataset.key
                ),
                None,
            )
            if matching_dataset_from_run_config is not None:
                dependencies.append(
                    Dependency(
                        depends_on=matching_dataset_from_run_config,
                        dependent=cli_dataset_generator,
                    )
                )

        # The `dataset_keys` are only filled if a dataset generator has a hard-coded
        # dataset as data source. If it's dynamic (i.e. filled at runtime), then
        # it will be a placeholder string (e.g. `<<DYNAMIC_DATASET>>`) and will be later
        # filled through `dataset.generator_specification.dataset_generator_config`.
        if (dataset_keys := getattr(data_source, "dataset_keys", None)) is not None:
            if not isinstance(dataset_keys, list):
                raise CLIError(f"'dataset_keys' must be a list. File: '{config_file}'.")

            for dataset_key in dataset_keys:
                if not isinstance(dataset_key, str):
                    raise CLIError(
                        f"Each item in 'dataset_keys' must be a string. File: '{config_file}'."
                    )
                # We check whether the referenced dataset exists in this run
                # config. If not, it's not a dependency we need to resolve here.
                matching_dataset_from_run_config = next(
                    (
                        cli_dataset
                        for cli_dataset in cli_datasets
                        if dataset_key == cli_dataset.key
                    ),
                    None,
                )
                if matching_dataset_from_run_config is not None:
                    dependencies.append(
                        Dependency(
                            depends_on=matching_dataset_from_run_config,
                            dependent=cli_dataset_generator,
                        )
                    )


def _build_dataset_dependencies(
    *,
    dependencies: list[Dependency],
    cli_dataset_generators: list[CLICreateDatasetGenerator],
    cli_datasets: list[CLICreateDataset],
    dataset_generators_map: EntityByIdentifiersMap[StoredDatasetGenerator],
) -> None:
    for cli_dataset in cli_datasets:
        if (generator_spec := cli_dataset.generator_specification) is None:
            # Dataset is not generated by a dataset generator and thus cannot
            # have dependencies on dataset generators.
            continue

        # We check whether the referenced dataset generator (by dataset
        # generator key) exists in this run config. If not, it's not a
        # dependency we need to resolve here.
        if (
            matching_dataset_generator_from_run_config := next(
                (
                    cli_dataset_generator
                    for cli_dataset_generator in cli_dataset_generators
                    if generator_spec.dataset_generator_key == cli_dataset_generator.key
                ),
                None,
            )
        ) is not None:
            dependencies.append(
                Dependency(
                    depends_on=matching_dataset_generator_from_run_config,
                    dependent=cli_dataset,
                )
            )
        matching_existing_dataset_generator = dataset_generators_map.get_entity_by_key(
            generator_spec.dataset_generator_key
        )
        # The new dataset generator from the current run takes precedence as
        # it might contain more recent configuration.
        if (
            matching_dataset_generator := (
                matching_dataset_generator_from_run_config
                or matching_existing_dataset_generator
            )
        ) is None:
            # Dataset is generated by a dataset generator which does not exist
            # and is also not being created in this run. We do not have dependencies
            # to resolve in this case, and we let it fail later.
            continue

        for (
            generator_config_key,
            generator_config_value,
        ) in generator_spec.dataset_generator_config.items():
            is_dataset_type_generator_config = any(
                parameter_spec.key == generator_config_key
                and parameter_spec.type == "dataset"
                for parameter_spec in matching_dataset_generator.config_spec
            )

            if (
                is_dataset_type_generator_config
                and (
                    # We check whether the referenced dataset exists in this run
                    # config. If not, it's not a dependency we need to resolve here.
                    matching_dataset_from_run_config := next(
                        (
                            cli_dataset
                            for cli_dataset in cli_datasets
                            if generator_config_value == cli_dataset.key
                        ),
                        None,
                    )
                )
                is not None
            ):
                dependencies.append(
                    Dependency(
                        depends_on=matching_dataset_from_run_config,
                        dependent=cli_dataset,
                    )
                )


def get_run_config_processing_order(
    *, cli_run_config: CLICreateRunConfig, dependencies: list[Dependency]
) -> list[
    CLICreateModelAdapter
    | CLICreateModel
    | CLICreateProviderAndModelKey
    | CLICreateDatasetGenerator
    | CLICreateDataset
    | CLICreateTask
    | CLICreateEvaluation
]:
    entities_to_be_ordered: list[CrossDependentEntities] = (
        cli_run_config.dataset_generators + cli_run_config.datasets
    )
    entity_by_node_id = {
        _get_node_id(entity): entity for entity in entities_to_be_ordered
    }
    entity_node_id_list = list(entity_by_node_id.keys())
    outgoing: dict[NodeId, list[NodeId]] = {
        node_id: [] for node_id in entity_node_id_list
    }
    indegree: dict[NodeId, int] = {node_id: 0 for node_id in entity_node_id_list}

    for dependency in dependencies:
        outgoing[_get_node_id(dependency.depends_on)].append(
            _get_node_id(dependency.dependent)
        )
        indegree[_get_node_id(dependency.dependent)] += 1

    entity_node_id_queue = deque(
        sorted(
            (node_id for node_id in entity_node_id_list if indegree[node_id] == 0),
            key=_cross_entity_type_priority,
        )
    )
    ordered_entity_node_ids = []

    while entity_node_id_queue:
        entity_node_id = entity_node_id_queue.popleft()
        ordered_entity_node_ids.append(entity_node_id)
        freed_this_round = []
        for dependent in outgoing[entity_node_id]:
            indegree[dependent] -= 1
            if indegree[dependent] == 0:
                freed_this_round.append(dependent)

        for node_id in sorted(freed_this_round, key=_cross_entity_type_priority):
            entity_node_id_queue.append(node_id)

    if len(ordered_entity_node_ids) != len(entity_node_id_list):
        remaining = [
            node_id for node_id in entity_node_id_list if indegree[node_id] > 0
        ]
        # NOTE: We raise error about circular dependency here, because
        # we should not have any other reason for topological sort to fail,
        # as we have already filtered entities to only those being created in this run.
        raise CLIError(
            "Circular dependency detected when trying to determine"
            f" order of creation and update. Remaining entities: {remaining}"
        )

    # NOTE: For now we only care about ordering dataset generators and datasets,
    # as those are the only entities that can have dependencies in the run config.
    # For the other entities, we want to have a static order (the one defined
    # in the run config file), so we prepend them (model adapters and models) or append
    # them (tasks and evaluation) to the ordered list.
    return (
        cli_run_config.model_adapters
        + cli_run_config.models
        + [entity_by_node_id[node_id] for node_id in ordered_entity_node_ids]
        + cli_run_config.tasks
        + ([cli_run_config.evaluation] if cli_run_config.evaluation else [])
    )
