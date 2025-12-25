from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Callable
from typing import cast

import questionary
import typer
from requests.structures import CaseInsensitiveDict

import latticeflow.go.cli.utils.arguments as cli_args
import latticeflow.go.cli.utils.exceptions as cli_exc
import latticeflow.go.cli.utils.printing as cli_print
from latticeflow.go.cli.utils.dtypes import CLICreateModel
from latticeflow.go.cli.utils.helpers import create_single_entity
from latticeflow.go.cli.utils.helpers import dump_entity_to_yaml_file
from latticeflow.go.cli.utils.helpers import get_client_from_env
from latticeflow.go.cli.utils.helpers import get_files_at_path
from latticeflow.go.cli.utils.helpers import is_update_payload_same_as_existing_entity
from latticeflow.go.cli.utils.helpers import register_app_callback
from latticeflow.go.cli.utils.helpers import update_single_entity
from latticeflow.go.cli.utils.schema_mappers import EntityByIdentifiersMap
from latticeflow.go.cli.utils.schema_mappers import map_model_api_to_cli_entity
from latticeflow.go.cli.utils.schema_mappers import map_model_cli_to_api_entity
from latticeflow.go.cli.utils.yaml_utils import load_yaml_recursively
from latticeflow.go.client import Client
from latticeflow.go.models import IntegrationModelProviderId
from latticeflow.go.models import MLTask
from latticeflow.go.models import Modality
from latticeflow.go.models import Model
from latticeflow.go.models import ModelAdapterInput
from latticeflow.go.models import ModelAdapterTransformationError
from latticeflow.go.models import ModelCustomConnectionConfig
from latticeflow.go.models import ModelProviderConnectionConfig
from latticeflow.go.models import RawModelInput
from latticeflow.go.models import RawModelOutput
from latticeflow.go.models import StoredModel
from latticeflow.go.models import StoredModelAdapter
from latticeflow.go.types import ApiError


_MODEL_PROVIDER_AND_KEY_REGEX = re.compile(
    r"^(?:(?P<provider>(?:together|zenguard|gemini|openai|fireworks|sambanova|anthropic|novita)[a-z0-9_-]*)/)?"
    r"(?P<model_key>[A-Za-z0-9._\-:@]+)$"
)
PRETTY_ENTITY_NAME = "model"
TABLE_COLUMNS: list[tuple[str, Callable[[StoredModel], str]]] = [
    ("Key", lambda model: model.key),
    ("Name", lambda model: model.display_name),
    (
        "URL",
        lambda model: model.config.url
        if isinstance(model.config, ModelCustomConnectionConfig)
        else "",
    ),
]
model_app = typer.Typer(help="Model commands")
register_app_callback(model_app)


@model_app.command("list")
def list_models(is_json_output: bool = cli_args.json_flag_option) -> None:
    """List all models as JSON or in a table."""
    if is_json_output:
        cli_print.suppress_logging()

    client = get_client_from_env()
    try:
        stored_models = client.models.get_models().models
        model_adapters_map = EntityByIdentifiersMap(
            client.model_adapters.get_model_adapters().model_adapters
        )
        cli_models = [
            map_model_api_to_cli_entity(
                stored_model=stored_model, model_adapters_map=model_adapters_map
            )
            for stored_model in stored_models
        ]
        if is_json_output:
            cli_print.print_entities_as_json(cli_models)
        else:
            cli_print.print_table("Models", cli_models, TABLE_COLUMNS)
    except Exception as error:
        raise cli_exc.CLIListError(PRETTY_ENTITY_NAME) from error


@model_app.command("add")
def _add(
    path: Path | None = cli_args.glob_config_path_option(
        PRETTY_ENTITY_NAME, is_required=False
    ),
    model_provider_and_key: str | None = typer.Option(
        None,
        "-p",
        "--provider",
        help=(
            "The model provider and model key in the format "
            "'`<provider_id>`/`<model_key>`' to integrate a model from a third-party "
            "provider (e.g. 'openai/gpt-4o'). The model key must match the provider's "
            "official model key/ID, as it is what will be sent to the provider during inference."
        ),
    ),
    should_validate_only: bool = cli_args.should_validate_only_option,
) -> None:
    """Create/update model(s) either based on YAML configuration(s) or from a third-
    party provider."""
    is_provider_model = model_provider_and_key is not None
    if path is None and model_provider_and_key is None:
        is_provider_model = (
            questionary.select(
                "What type of model to add:", choices=["custom", "provider"]
            ).ask()
            == "provider"
        )

    client = get_client_from_env()
    models_map = EntityByIdentifiersMap(client.models.get_models().models)
    if is_provider_model:
        add_model_from_provider(model_provider_and_key, models_map, client)
        return

    if path is None:
        path = questionary.path(
            "Enter path to the model definition YAML (tab for autocomplete):"
        ).ask()
    _add_custom_models(
        path=Path(path), should_validate_only=should_validate_only, client=client
    )


def _add_custom_models(
    *, path: Path, should_validate_only: bool, client: Client
) -> None:
    """Create/update model(s) based on YAML configuration(s)."""
    if not (config_files := get_files_at_path(path)):
        raise cli_exc.CLIConfigNotFoundError(PRETTY_ENTITY_NAME, path)

    if should_validate_only:
        _validate_models(config_files)
        return

    models_map = EntityByIdentifiersMap(client.models.get_models().models)
    model_adapters_map = EntityByIdentifiersMap(
        client.model_adapters.get_model_adapters().model_adapters
    )
    is_creating_single_entity = len(config_files) == 1
    failures = 0
    for config_file in config_files:
        try:
            cli_model = _get_cli_model_from_file(config_file)
            new_stored_model = map_and_add_single_custom_model(
                client=client,
                cli_model=cli_model,
                model_adapters_map=model_adapters_map,
                models_map=models_map,
                config_file=config_file,
            )
            models_map.update_entity(new_stored_model)
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


def map_and_add_single_custom_model(
    *,
    client: Client,
    cli_model: CLICreateModel,
    model_adapters_map: EntityByIdentifiersMap[StoredModelAdapter],
    models_map: EntityByIdentifiersMap[StoredModel],
    config_file: Path,
    verbosity: cli_print.Verbosity = "high",
) -> StoredModel:
    model = map_model_cli_to_api_entity(
        cli_model=cli_model,
        model_adapters_map=model_adapters_map,
        config_file=config_file,
    )
    stored_model = models_map.get_entity_by_key(model.key)
    if stored_model and is_update_payload_same_as_existing_entity(model, stored_model):
        cli_print.log_no_change_info(PRETTY_ENTITY_NAME, model.key, verbosity=verbosity)
        return stored_model
    elif stored_model:
        return update_single_entity(
            pretty_entity_name=PRETTY_ENTITY_NAME,
            update_fn=lambda: client.models.update_model(stored_model.id, model),
            entity_identifier_value=stored_model.key,
            verbosity=verbosity,
        )
    else:
        return create_single_entity(
            pretty_entity_name=PRETTY_ENTITY_NAME,
            create_fn=lambda: client.models.create_model(model),
            entity_identifier_value=model.key,
            verbosity=verbosity,
        )


def add_model_from_provider(
    model_provider_and_key: str | None,
    models_map: EntityByIdentifiersMap[StoredModel],
    client: Client,
    verbosity: cli_print.Verbosity = "high",
) -> StoredModel:
    """Integrate a model from a third-party provider (e.g. OpenAI)."""
    if model_provider_and_key is not None:
        selected_model = _get_provider_model_from_cli_parameter(
            model_provider_and_key, client
        )
    else:
        selected_model = _get_provider_model_interactively(client)

    if (existing_model := models_map.get_entity_by_key(selected_model.key)) is not None:
        cli_print.log_model_already_integrated_info(
            cast(
                ModelProviderConnectionConfig, selected_model.config
            ).provider_id.value,
            selected_model.display_name,
            selected_model.key,
            verbosity=verbosity,
        )
        return existing_model

    created_model = client.models.create_model(selected_model)
    cli_print.log_model_integration_success_info(
        cast(ModelProviderConnectionConfig, created_model.config).provider_id.value,
        created_model.display_name,
        created_model.key,
        verbosity=verbosity,
    )
    return created_model


def _get_provider_model_from_cli_parameter(
    model_provider_and_key: str, client: Client
) -> Model:
    """Integrate a model from a third-party provider (e.g. OpenAI) using a provided
    string containing both the provider and the model key."""
    if not (match := _MODEL_PROVIDER_AND_KEY_REGEX.fullmatch(model_provider_and_key)):
        raise cli_exc.CLIModelIntegrationError(
            f"Given model provider and key '{model_provider_and_key}' has invalid format."
            " Must be in the format `<provider_id>/<model_key>`, where `<provider_id>` is one of: "
            + ", ".join(
                f"`{provider_id.value}`" for provider_id in IntegrationModelProviderId
            )
        )
    selected_provider_id = IntegrationModelProviderId(match.group("provider"))
    model_key = match.group("model_key")

    _validate_model_provider_is_integrated(selected_provider_id, client)

    try:
        models = client.models.get_model_provider(selected_provider_id.value).models
    except Exception as error:
        raise cli_exc.CLIModelIntegrationError(
            f"Could not get models from provider '{selected_provider_id.value}'."
        ) from error

    if (
        matching_model := next(
            (model for model in models if model.display_name == model_key), None
        )
    ) is not None:
        return matching_model

    raise cli_exc.CLIModelIntegrationError(
        f"Could not get model '{model_key}' from provider '{selected_provider_id.value}'."
        " Make sure the model key is correct."
    )


def _get_provider_model_interactively(client: Client) -> Model:
    """Integrate a model from a third-party provider (e.g. OpenAI) using an interactive
    CLI appication."""
    selected_provider_id = IntegrationModelProviderId(
        questionary.select(
            "Select the provider of the model:",
            choices=[provider_id.value for provider_id in IntegrationModelProviderId],
        ).ask()
    )

    _validate_model_provider_is_integrated(selected_provider_id, client)

    try:
        models = client.models.get_model_provider(selected_provider_id.value).models
    except Exception as error:
        raise cli_exc.CLIModelIntegrationError(
            f"Could not get models from provider '{selected_provider_id.value}'."
        ) from error

    selected_model_name = questionary.autocomplete(
        "Select the model to integrate (Press Tab to see all models):",
        choices=[model.display_name for model in models],
        match_middle=True,
    ).ask()

    return next(
        (model for model in models if model.display_name == selected_model_name)
    )


@model_app.command("delete")
def _delete(key: str = cli_args.delete_key_argument(PRETTY_ENTITY_NAME)) -> None:
    """Delete the model with the provided key."""
    client = get_client_from_env()
    try:
        cli_print.log_delete_attempt_info(PRETTY_ENTITY_NAME, key)
        client.models.delete_model_by_key(key=key)
        cli_print.log_delete_success_info(PRETTY_ENTITY_NAME, key)
    except Exception as error:
        raise cli_exc.CLIDeleteError(PRETTY_ENTITY_NAME, key) from error


@model_app.command("export")
def _export(
    key: str = cli_args.export_key_argument(PRETTY_ENTITY_NAME),
    output: Path | None = cli_args.export_output_path_option,
) -> None:
    """Export the model with the provided key to a file or print as JSON."""
    if not output:
        cli_print.suppress_logging()

    client = get_client_from_env()
    try:
        stored_model = client.models.get_model_by_key(key=key)
        cli_model = map_model_api_to_cli_entity(
            stored_model=stored_model,
            model_adapters_map=EntityByIdentifiersMap(
                client.model_adapters.get_model_adapters().model_adapters
            ),
        )
        if output:
            dump_entity_to_yaml_file(output, cli_model)
            cli_print.log_export_success_info(PRETTY_ENTITY_NAME, output, key)
        else:
            cli_print.print_entities_as_json(cli_model)
    except Exception as error:
        raise cli_exc.CLIExportError(
            PRETTY_ENTITY_NAME, key, output_path=output
        ) from error


@model_app.command("test")
def _test(
    key: str = cli_args.test_configuration_key_argument(PRETTY_ENTITY_NAME),
    model_input_path: Path | None = typer.Option(
        None,
        "--model-input",
        help="Path to a JSON file with a model input in LatticeFlow AI format."
        "If not provided, default is used, for more details see "
        "https://aigo.latticeflow.io/docs/model-io.",
        callback=cli_args.check_path_not_emtpy,
    ),
) -> None:
    """Test model connection, inference and I/O adapter mapping of the model with the
    provided key."""
    client = get_client_from_env(read_timeout=60.0)
    try:
        stored_model = client.models.get_model_by_key(key)
        model_input = _get_test_model_input(model_input_path, stored_model)
        cli_print.log_info("1. Checking connection to model.")
        _check_connection(client, stored_model.key, stored_model)
        cli_print.log_char_full_width("=")
        cli_print.log_info("2. Transforming model input.")
        stored_model_adapter = client.model_adapters.get_model_adapter(
            stored_model.adapter_id
        )
        raw_model_input = _transform_model_input(
            client, model_input, stored_model, stored_model_adapter
        )
        cli_print.log_char_full_width("=")
        cli_print.log_info("3. Running inference.")
        raw_model_output = _run_model_inference(client, stored_model, raw_model_input)
        cli_print.log_char_full_width("=")
        cli_print.log_info("4. Transforming model output.")
        _transform_model_output(
            client, stored_model, stored_model_adapter, raw_model_output
        )
        cli_print.log_char_full_width("=")
        cli_print.log_test_success_info(PRETTY_ENTITY_NAME, key)
    except Exception as error:
        raise cli_exc.CLITestConfigurationError(PRETTY_ENTITY_NAME, key) from error


def _get_cli_model_from_file(config_file: Path) -> CLICreateModel:
    try:
        loaded_dict, _ = load_yaml_recursively(config_file)
        return CLICreateModel.model_validate(loaded_dict, ignore_extra=False)
    except Exception as error:
        raise cli_exc.CLIInvalidConfigError(
            PRETTY_ENTITY_NAME, config_file, "models"
        ) from error


def _check_connection(client: Client, key: str, stored_model: StoredModel) -> None:
    if isinstance(stored_model.config, ModelCustomConnectionConfig):
        api_key_as_string_or_none = (
            stored_model.config.api_key.get_secret_value()
            if stored_model.config.api_key
            else None
        )
        cli_print.log_info(
            (
                f"- Key: {key}\n"
                f"- URL: {stored_model.config.url}\n"
                f"- API key: {api_key_as_string_or_none}\n"
                f"- Model key: {stored_model.config.model_key}"
            )
        )
    elif isinstance(stored_model.config, ModelProviderConnectionConfig):
        cli_print.log_info(
            (
                f"- Key: {key}\n"
                f"- Provider ID: {stored_model.config.provider_id}\n"
                f"- Model key: {stored_model.config.model_key}"
            )
        )

    connection_check_result = client.models.check_model_connection(stored_model.id)
    returned_message = (
        f"\nReturned message: {connection_check_result.message}"
        if connection_check_result.message
        else ""
    )
    if not connection_check_result.success:
        raise cli_exc.CLIError(
            f"Connection to model with key '{key}' was not successful.{returned_message}"
        )

    cli_print.log_info(
        f"Successfully connected to model with key '{key}'.{returned_message}"
    )


def _transform_model_input(
    client: Client,
    model_input: str,
    stored_model: StoredModel,
    stored_model_adapter: StoredModelAdapter,
) -> RawModelInput:
    cli_print.log_info(f"Model input in LatticeFlow AI format:\n{model_input}")
    cli_print.log_char_full_width("-")

    if stored_model_adapter.process_input:
        cli_print.log_info(
            f"Jinja input transform (from adapter "
            f"'{stored_model_adapter.display_name}'):\n"
            f"{stored_model_adapter.process_input.source_code}"
        )
        cli_print.log_char_full_width("-")

    try:
        raw_model_input = client.models.transform_input_model(
            stored_model.id, ModelAdapterInput(input=model_input)
        )
    except ApiError as error:
        if isinstance(error.error, ModelAdapterTransformationError):
            transformed_suffix = (
                f", {error.error.transformed}" if error.error.transformed else ""
            )
            raise cli_exc.CLIError(
                f"{error.error.message}{transformed_suffix}"
            ) from error
        raise

    cli_print.log_info(
        "Model input in the format expected by the model "
        f"(used for inference):\n{raw_model_input.input}"
    )

    return raw_model_input


def _format_headers(headers: dict[str, str]) -> str:
    return "\n".join(f"  {key}: {value}" for key, value in headers.items())


def _run_model_inference(
    client: Client, stored_model: StoredModel, raw_model_input: RawModelInput
) -> RawModelOutput:
    raw_model_output = client.models.run_model_inference(
        stored_model.id, body=raw_model_input
    )
    cli_print.log_info(
        f"Request headers:\n{_format_headers(raw_model_output.request_headers)}"
    )
    cli_print.log_char_full_width("-")

    # If the input headers specify that the input is JSON, verify that it is valid JSON.
    if (
        CaseInsensitiveDict(raw_model_output.request_headers).get("Content-Type")
        == "application/json"
    ):
        try:
            json.loads(raw_model_input.input)
        except json.JSONDecodeError as e:
            cli_print.log_warning(
                "The model input is not valid JSON, "
                "even though the request header specifies 'application/json'.\nError: "
                f"{str(e)}\nLine: {e.doc.splitlines()[e.lineno - 1]}\n"
                f"{' ' * (e.colno - 1 + 6)}^"
            )
            cli_print.log_char_full_width("-")

    cli_print.log_info(f"Status code: {raw_model_output.status_code}")
    cli_print.log_info(
        f"Response headers:\n{_format_headers(raw_model_output.response_headers)}"
    )
    return raw_model_output


def _transform_model_output(
    client: Client,
    stored_model: StoredModel,
    stored_model_adapter: StoredModelAdapter,
    raw_model_output: RawModelOutput,
) -> None:
    cli_print.log_info(
        f"Model output in the format returned by the model:\n{raw_model_output.output}"
    )
    cli_print.log_char_full_width("-")

    try:
        transformed_output = client.models.transform_output_model(
            stored_model.id, raw_model_output
        )
    except ApiError as error:
        if isinstance(error.error, ModelAdapterTransformationError):
            transformed_suffix = (
                f", {error.error.transformed}" if error.error.transformed else ""
            )
            raise cli_exc.CLIError(
                f"{error.error.message}{transformed_suffix}"
            ) from error
        raise

    if stored_model_adapter.process_output:
        cli_print.log_info(
            "Jinja output transform (from adapter "
            f"'{stored_model_adapter.display_name}'):\n"
            f"{stored_model_adapter.process_output.source_code}"
        )
        cli_print.log_char_full_width("-")

    cli_print.log_info(
        f"Model output in the format expected by LatticeFlow AI:\n{transformed_output}"
    )


def _get_test_model_input(
    model_input_path: Path | None, stored_model: StoredModel
) -> str:
    if model_input_path:
        if not model_input_path.is_file():
            raise cli_exc.CLIInvalidSingleFilePathError(model_input_path)

        return model_input_path.read_text()
    else:
        if (stored_model.modality, stored_model.task) == (
            Modality.TEXT,
            MLTask.CHAT_COMPLETION,
        ):
            return '{"messages": [{"role": "user", "content": "Hello!"}]}'

        raise cli_exc.CLIError(
            f"Model testing for modality '{stored_model.modality.value}' "
            f"and task '{stored_model.task.value}' "
            f"requires model input to be specified and passed with `--model-input`."
        )


def _validate_models(config_files: list[Path]) -> None:
    for config_file in config_files:
        try:
            _get_cli_model_from_file(config_file)
            cli_print.log_validation_success_info(config_file)
        except Exception as error:
            raise cli_exc.CLIValidationError(PRETTY_ENTITY_NAME) from error


def _validate_model_provider_is_integrated(
    model_provider_id: IntegrationModelProviderId, client: Client
) -> None:
    if not any(
        stored_integration.id == model_provider_id
        and stored_integration.config is not None
        for stored_integration in client.integrations.get_integrations().integrations
    ):
        raise cli_exc.CLIModelIntegrationError(
            f"Model integration for provider '{model_provider_id.value}' not found."
            f" Please run `lf integration add --provider {model_provider_id.value}` to add the integration."
        )
