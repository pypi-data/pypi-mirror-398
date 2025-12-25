from __future__ import annotations

import questionary
import typer
from pydantic import SecretStr

import latticeflow.go.cli.utils.exceptions as cli_exc
from latticeflow.go.cli.utils.helpers import get_client_from_env
from latticeflow.go.cli.utils.helpers import register_app_callback
from latticeflow.go.models import Integration
from latticeflow.go.models import IntegrationModelProviderId
from latticeflow.go.models import OpenAIIntegration
from latticeflow.go.models import ZenguardIntegration
from latticeflow.go.models import ZenguardTier


PRETTY_ENTITY_NAME = "integration"
integration_app = typer.Typer(help="Third-party integration commands")
register_app_callback(integration_app)


@integration_app.command("add")
def _add(
    provider: IntegrationModelProviderId | None = typer.Option(
        None, help="The provider's integration ID."
    ),
    integration_api_key: str | None = typer.Option(
        None, "--api-key", help="The API key for the provider"
    ),
    zenguard_tier: ZenguardTier | None = typer.Option(
        None,
        "--zenguard-tier",
        help="The ZenGuard tier to use. Only applicable if integration is 'zenguard'.",
    ),
) -> None:
    """Configure a third-party provider integration."""
    integration_id = provider
    if integration_id is None:
        selection = questionary.select(
            "Select an integration:",
            choices=[provider_id.value for provider_id in IntegrationModelProviderId],
        ).ask()
        integration_id = IntegrationModelProviderId(selection)

    if integration_api_key is None:
        integration_api_key = questionary.text(
            "Enter the API key for the integration:"
        ).ask()

    client = get_client_from_env()
    try:
        if integration_id == IntegrationModelProviderId.OPENAI:
            client.integrations.update_open_ai_integration(
                OpenAIIntegration(api_key=SecretStr(integration_api_key))
            )
        elif integration_id == IntegrationModelProviderId.ZENGUARD:
            if zenguard_tier is None:
                zenguard_tier_selection = questionary.select(
                    "Select a ZenGuard tier:",
                    choices=[tier.value for tier in ZenguardTier],
                ).ask()
                zenguard_tier = ZenguardTier(zenguard_tier_selection)

            client.integrations.update_zenguard_integration(
                ZenguardIntegration(
                    api_key=SecretStr(integration_api_key), tier=zenguard_tier
                )
            )
        else:
            client.integrations.update_integration(
                integration_id.value,
                Integration(api_key=SecretStr(integration_api_key)),
            )
    except Exception as error:
        raise cli_exc.CLIIntegrateProviderError(integration_id) from error
