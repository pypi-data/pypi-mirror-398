from __future__ import annotations

from pathlib import Path

from latticeflow.go.models import IntegrationModelProviderId


class CLIError(Exception):
    pass


class CLIConfigurationError(CLIError):
    pass


class CLIInitError(CLIError):
    def __init__(self) -> None:
        super().__init__("Failed to initialize single-tenant deployment.")


class CLIListError(CLIError):
    def __init__(self, entity_name: str) -> None:
        super().__init__(f"Failed to list {entity_name} entities.")


class CLIValidationError(CLIError):
    def __init__(self, entity_name: str) -> None:
        super().__init__(
            f"Validation failed for one or more {entity_name} configurations."
        )


class CLICreateUpdateSingleEntityError(CLIError):
    def __init__(self, entity_name: str, path: Path) -> None:
        super().__init__(f"Could not create/update {entity_name} from path '{path}'.")


class CLICreateUpdateAllFailedError(CLIError):
    def __init__(self, entity_name: str, path: Path) -> None:
        super().__init__(
            f"Could not create/update any {entity_name} loaded using glob '{path}'."
        )


class CLICreateError(CLIError):
    def __init__(
        self,
        entity_name: str,
        identifier_value: str,
        identifier_type: str = "key",
        additional_message: str = "",
    ) -> None:
        super().__init__(
            f"Failed to create {entity_name} with {identifier_type} '{identifier_value}'."
            f"{additional_message}"
        )


class CLIUpdateError(CLIError):
    def __init__(
        self,
        entity_name: str,
        identifier_value: str,
        identifier_type: str = "key",
        additional_message: str = "",
    ) -> None:
        super().__init__(
            f"Failed to update {entity_name} with {identifier_type} '{identifier_value}'."
            f"{additional_message}"
        )


class CLIDeleteError(CLIError):
    def __init__(
        self,
        entity_name: str,
        identifier_value: str,
        identifier_type: str = "key",
        additional_message: str = "",
    ) -> None:
        super().__init__(
            f"Failed to delete {entity_name} with {identifier_type} '{identifier_value}'."
            f"{additional_message}"
        )


class CLIExportError(CLIError):
    def __init__(
        self,
        entity_name: str,
        identifier_value: str,
        identifier_type: str = "key",
        output_path: Path | None = None,
        additional_message: str = "",
    ) -> None:
        output_path_info = f" to {output_path}" if output_path else ""
        super().__init__(
            f"Failed to export {entity_name} with {identifier_type} '{identifier_value}'"
            f"{output_path_info}.{additional_message}"
        )


class CLITestConfigurationError(CLIError):
    def __init__(
        self,
        entity_name: str,
        identifier_value: str,
        identifier_type: str = "key",
        additional_message: str = "",
    ) -> None:
        super().__init__(
            f"Failed to test configuration of {entity_name} with {identifier_type}"
            f" '{identifier_value}'.{additional_message}"
        )


class CLIGenerateDatasetPreviewFromPathError(CLIError):
    def __init__(self, path: Path, additional_message: str = "") -> None:
        super().__init__(
            f"Failed to generate preview for dataset from path '{path}'.{additional_message}"
        )


class CLIOverviewEvaluationError(CLIError):
    def __init__(self, id: str) -> None:
        super().__init__(
            f"Failed to show an overview of the evaluation with ID '{id}'."
        )


class CLIDownloadEvaluationError(CLIError):
    def __init__(self, id: str) -> None:
        super().__init__(
            f"Failed to download results of the evaluation with ID '{id}'."
        )


class CLIConfigNotFoundError(CLIError):
    def __init__(self, entity_name: str, path: Path) -> None:
        super().__init__(f"No config for {entity_name} found at '{path}'.")


class CLIInvalidConfigError(CLIError):
    def __init__(
        self, entity_name: str, path: Path | None, entity_url_suffix: str | None
    ) -> None:
        docs_hint = ""
        if entity_url_suffix:
            docs_url = (
                f"https://aigo.latticeflow.io/docs/cli-reference-{entity_url_suffix}"
            )
            docs_hint = (
                f" Check the CLI model reference at {docs_url} "
                "to see the required schema for the YAML config."
            )
        path_info = f" at path '{path}'" if path else ""
        message = f"Invalid {entity_name} config{path_info}.{docs_hint}"
        super().__init__(message)


class CLIEntityMappingError(CLIError):
    def __init__(self, entity_name: str, path: Path | None) -> None:
        path_suffix = f" from the config at path '{path}'" if path else ""
        super().__init__(f"Could not map {entity_name}{path_suffix}.")


class CLIDatasetDownloadError(CLIError):
    def __init__(self, key: str) -> None:
        super().__init__(f"Could not download data for dataset with key '{key}'.")


class CLIDatasetSaveError(CLIError):
    def __init__(self, key: str) -> None:
        super().__init__(f"Failed to save data for dataset with key '{key}'.")


class CLIInvalidSingleFilePathError(CLIError):
    def __init__(self, path: Path) -> None:
        super().__init__(f"'{path}' is not a path to a single file.")


class CLIUserRoleParsingError(CLIError):
    def __init__(self, roles: str) -> None:
        super().__init__(f"Could not parse roles '{roles}'.")


class CLIResetUserPasswordError(CLIError):
    def __init__(self) -> None:
        super().__init__("Failed to reset user credentials.'")


class CLIIntegrateProviderError(CLIError):
    def __init__(self, integration_id: IntegrationModelProviderId) -> None:
        super().__init__(f"Failed to integrate provider '{integration_id}'.")


class CLIMissingAppContextError(CLIError):
    def __init__(self) -> None:
        super().__init__(
            "AI app context is not set. Set it by running `lf switch 'my-app'`."
        )


class CLIModelIntegrationError(CLIError):
    def __init__(self, additional_message: str) -> None:
        super().__init__(f"Failed to integrate provider model. {additional_message}")
