from __future__ import annotations

from typing import Callable

import requests
import typer
from pydantic import SecretStr

import latticeflow.go.cli.utils.arguments as cli_args
import latticeflow.go.cli.utils.exceptions as cli_exc
import latticeflow.go.cli.utils.printing as cli_print
from latticeflow.go import Client
from latticeflow.go.cli.utils.constants import LF_AIGO_PASS_NAME
from latticeflow.go.cli.utils.env_vars import get_init_setup_cli_env_vars
from latticeflow.go.cli.utils.env_vars import get_tenant_cli_env_vars
from latticeflow.go.cli.utils.helpers import create_single_entity
from latticeflow.go.cli.utils.helpers import get_client_from_env
from latticeflow.go.cli.utils.helpers import register_app_callback
from latticeflow.go.models import CredentialType
from latticeflow.go.models import InitialSetupRequest
from latticeflow.go.models import PasswordUserCredential
from latticeflow.go.models import ResetUserCredentialAction
from latticeflow.go.models import State
from latticeflow.go.models import StoredTenant
from latticeflow.go.models import StoredUser
from latticeflow.go.models import Tenant
from latticeflow.go.models import User


PRETTY_ENTITY_NAME = "tenant"
TENANT_TABLE_COLUMNS: list[tuple[str, Callable[[StoredTenant], str]]] = [
    ("ID", lambda tenant: tenant.id),
    ("Name", lambda tenant: tenant.name),
    ("Alias", lambda tenant: tenant.alias),
    ("Domains", lambda tenant: ", ".join(tenant.domains)),
]
USER_TABLE_COLUMNS: list[tuple[str, Callable[[StoredUser], str]]] = [
    ("ID", lambda user: user.id),
    ("Email", lambda user: user.email),
    ("Name", lambda user: user.name),
    ("Enabled", lambda user: str(user.enabled)),
    ("Roles", lambda user: ", ".join([role.value for role in user.roles])),
]
tenant_app = typer.Typer(help="Control plane (tenant & user) commands")
register_app_callback(tenant_app, get_tenant_cli_env_vars, skipped_subcommands={"init"})
register_app_callback(
    tenant_app, get_init_setup_cli_env_vars, included_subcommands={"init"}
)


@tenant_app.command(name="list")
def _list(is_json_output: bool = cli_args.json_flag_option) -> None:
    """List all tenants as JSON or in a table."""
    if is_json_output:
        cli_print.suppress_logging()

    client = get_client_from_env(get_tenant_cli_env_vars)
    try:
        stored_tenants = client.tenants.get_tenants().tenants
        if is_json_output:
            cli_print.print_entities_as_json(stored_tenants)
        else:
            cli_print.print_table("Tenants", stored_tenants, TENANT_TABLE_COLUMNS)
    except Exception as error:
        raise cli_exc.CLIListError(PRETTY_ENTITY_NAME) from error


@tenant_app.command(name="add")
def _add(
    name: str = typer.Option(
        ..., help="A unique name for the tenant. Example: 'My Organization'."
    ),
    alias: str = typer.Option(
        ...,
        help="A unique identifier for the tenant (allowed [a-z0-9-]). Example: 'my-org'.",
    ),
    domains: str = typer.Option(
        ...,
        help=(
            "The internet domain(s) associated with the tenant (comma-separated)."
            "Example: 'latticeflow.ai,latticeflow.org'."
        ),
    ),
) -> None:
    """Create a new tenant."""
    client = get_client_from_env(get_tenant_cli_env_vars)
    try:
        create_single_tenant(
            client,
            Tenant(
                name=name,
                alias=alias,
                domains=[domain.strip() for domain in domains.split(",")],
            ),
        )
    except Exception as error:
        raise cli_exc.CLICreateError(PRETTY_ENTITY_NAME, alias, "alias") from error


@tenant_app.command(name="delete")
def _delete(
    alias: str = typer.Option(
        ..., help="Alias of the tenant to be deleted. Example: 'my-org'."
    ),
) -> None:
    """Delete the tenant with the provided alias."""
    client = get_client_from_env(get_tenant_cli_env_vars)
    try:
        client.tenants.delete_tenant_by_alias(alias)
        cli_print.log_delete_success_info(PRETTY_ENTITY_NAME, alias, "alias")
    except Exception as error:
        raise cli_exc.CLIDeleteError(PRETTY_ENTITY_NAME, alias, "alias") from error


@tenant_app.command(name="list-users")
def list_users(
    alias: str = typer.Option(
        ...,
        help="Alias of the tenant for which the user should be displayed. Example: 'my-org'.",
    ),
    is_json_output: bool = cli_args.json_flag_option,
) -> None:
    """List all users for the tenant with the provided alias as JSON or in a table."""
    client = get_client_from_env(get_tenant_cli_env_vars)
    try:
        stored_users = client.tenants.get_all_tenant_users_by_alias(alias).users
        if is_json_output:
            cli_print.print_entities_as_json(stored_users)
        else:
            cli_print.print_table(
                f"Users for tenant with alias '{alias}'",
                stored_users,
                USER_TABLE_COLUMNS,
            )
    except Exception as error:
        raise cli_exc.CLIListError(PRETTY_ENTITY_NAME) from error


@tenant_app.command("add-user")
def _add_user(
    tenant_alias: str = typer.Option(
        ...,
        help="Alias of the tenant for which the user should be created. Example: 'my-org'.",
    ),
    email: str = cli_args.create_user_email_option,
    name: str = cli_args.create_user_name_option,
    roles: str = cli_args.create_user_roles_option,
) -> None:
    """Create a user for the tenant with the provided alias."""
    parsed_roles = cli_args.parse_user_roles(roles)
    client = get_client_from_env(get_tenant_cli_env_vars)
    try:
        stored_tenant = client.tenants.get_tenant_by_alias(tenant_alias)
        stored_user = client.tenants.create_tenant_user(
            stored_tenant.id, User(email=email, name=name, roles=parsed_roles)
        )
        cli_print.log_create_success_info(
            "user", stored_user.email, "email", verbosity="high"
        )
    except Exception as error:
        raise cli_exc.CLICreateError("user", email, "email") from error

    try:
        _reset_user_password_helper(client, stored_tenant.id, stored_user)
    except Exception as error:
        raise cli_exc.CLIResetUserPasswordError() from error


@tenant_app.command(name="reset-password")
def _reset_password(
    tenant_alias: str = typer.Option(
        ..., help="Alias of the tenant to which the user belongs. Example: 'my-org'."
    ),
    email: str = cli_args.reset_password_email_option,
) -> None:
    """Reset the password for the user with the provided email."""
    client = get_client_from_env(get_tenant_cli_env_vars)
    try:
        stored_tenant = client.tenants.get_tenant_by_alias(tenant_alias)
        stored_user = client.tenants.get_tenant_user_by_email(email, tenant_alias)
        _reset_user_password_helper(client, stored_tenant.id, stored_user)
    except Exception as error:
        raise cli_exc.CLIResetUserPasswordError() from error


@tenant_app.command(name="init")
def _init(
    email: str = typer.Option(
        ..., help="A unique email for the user. Example: 'johndoe@latticeflow.ai'."
    ),
    name: str = typer.Option(
        ..., "--name", help="Name of the user. Example: 'John Doe'."
    ),
    password: str = typer.Option(
        ..., "--password", help="Password for the user.", envvar=LF_AIGO_PASS_NAME
    ),
) -> None:
    """Initialize the AI GO! single tenant setup."""
    aigo_url = get_init_setup_cli_env_vars()
    try:
        with requests.Session() as session:
            response = session.post(
                f"{aigo_url}/api/initial-setup",
                json=InitialSetupRequest(
                    name=name,
                    email=email,
                    credentials=PasswordUserCredential(
                        credential_type=CredentialType.password,
                        value=SecretStr(password),
                    ),
                ).model_dump(mode="json"),
            )
            if response.status_code == 400 and "already complete" in response.text:
                cli_print.log_info("Initial setup already complete.")
                return

            response.raise_for_status()
            response = session.get(f"{aigo_url}/api/state")
            response.raise_for_status()

            state = State.model_validate(response.json())
            if state.api_key is None:
                raise cli_exc.CLIConfigurationError(
                    "State did not contain the API key!"
                )

            cli_print.log_info(f"API key: '{state.api_key.get_secret_value()}'")
    except Exception as error:
        raise cli_exc.CLIInitError() from error


def _reset_user_password_helper(
    client: Client, tenant_id: str, stored_user: StoredUser
) -> None:
    password_user_credentials = client.tenants.reset_tenant_user_credential(
        tenant_id=tenant_id,
        user_id=stored_user.id,
        body=ResetUserCredentialAction(credential_type=CredentialType.password),
    )
    cli_print.log_info(f"Password reset for user with email '{stored_user.email}'.")
    cli_print.log_info(
        f"New password: {password_user_credentials.value.get_secret_value()}"
    )


def create_single_tenant(
    client: Client, tenant: Tenant, verbosity: cli_print.Verbosity = "high"
) -> StoredTenant:
    return create_single_entity(
        pretty_entity_name=PRETTY_ENTITY_NAME,
        create_fn=lambda: client.tenants.create_tenant(tenant),
        entity_identifier_value=tenant.alias,
        entity_identifier_type="alias",
        verbosity=verbosity,
    )
