from __future__ import annotations

from typing import Callable

import typer

import latticeflow.go.cli.utils.arguments as cli_args
import latticeflow.go.cli.utils.exceptions as cli_exc
import latticeflow.go.cli.utils.printing as cli_print
from latticeflow.go.cli.utils.helpers import create_single_entity
from latticeflow.go.cli.utils.helpers import get_client_from_env
from latticeflow.go.cli.utils.helpers import is_update_payload_same_as_existing_entity
from latticeflow.go.cli.utils.helpers import register_app_callback
from latticeflow.go.cli.utils.helpers import update_single_entity
from latticeflow.go.client import Client
from latticeflow.go.models import CredentialType
from latticeflow.go.models import ResetUserCredentialAction
from latticeflow.go.models import StoredUser
from latticeflow.go.models import User


PRETTY_ENTITY_NAME = "user"
USER_TABLE_COLUMN: list[tuple[str, Callable[[StoredUser], str]]] = [
    ("ID", lambda user: user.id),
    ("Email", lambda user: user.email),
    ("Name", lambda user: user.name),
    ("Enabled", lambda user: str(user.enabled)),
    ("Roles", lambda user: ", ".join([role.value for role in user.roles])),
]
user_app = typer.Typer(help="User commands")
register_app_callback(user_app)


@user_app.command(name="list")
def _list(is_json_output: bool = cli_args.json_flag_option) -> None:
    """List all users as JSON or in a table."""
    if is_json_output:
        cli_print.suppress_logging()

    client = get_client_from_env()
    try:
        stored_users = client.users.get_users().users
        if is_json_output:
            cli_print.print_entities_as_json(stored_users)
        else:
            cli_print.print_table("Users", stored_users, USER_TABLE_COLUMN)
    except Exception as error:
        raise cli_exc.CLIListError(PRETTY_ENTITY_NAME) from error


@user_app.command("add")
def _add(
    email: str = cli_args.create_user_email_option,
    name: str = cli_args.create_user_name_option,
    roles: str = cli_args.create_user_roles_option,
) -> None:
    """Create a new user or update it if a user with the provided email
    already exists."""
    parsed_roles = cli_args.parse_user_roles(roles)
    client = get_client_from_env()
    try:
        user = User(email=email, name=name, roles=parsed_roles)
        stored_user = next(
            (
                stored_user
                for stored_user in client.users.get_users().users
                if stored_user.email == email
            ),
            None,
        )
        if stored_user and is_update_payload_same_as_existing_entity(user, stored_user):
            cli_print.log_no_change_info(
                PRETTY_ENTITY_NAME, user.email, "email", verbosity="high"
            )
        elif stored_user:
            stored_user = update_single_user(client, stored_user, user)
        else:
            stored_user = create_single_user(client, user)
    except Exception as error:
        raise cli_exc.CLICreateError(PRETTY_ENTITY_NAME, email, "email") from error

    try:
        _reset_user_password_helper(client, stored_user)
    except Exception as error:
        raise cli_exc.CLIResetUserPasswordError() from error


@user_app.command("enable")
def _enable(
    email: str = typer.Option(
        ..., help="Email of the user to be enabled. Example: 'johndoe@latticeflow.ai'"
    ),
) -> None:
    """Enable the user with the provided email."""
    client = get_client_from_env()
    _set_user_status(client, email, True)


@user_app.command("disable")
def _disable(
    email: str = typer.Option(
        ..., help="Email of the user to be disabled. Example: 'johndoe@latticeflow.ai'"
    ),
) -> None:
    """Disable the user with the provided email."""
    client = get_client_from_env()
    _set_user_status(client, email, False)


@user_app.command("reset-password")
def _reset_password(email: str = cli_args.reset_password_email_option) -> None:
    """Reset the password for the user with the provided email."""
    client = get_client_from_env()
    try:
        stored_user = client.users.get_user_by_email(email)
        _reset_user_password_helper(client, stored_user)
    except Exception as error:
        raise cli_exc.CLIResetUserPasswordError() from error


def _reset_user_password_helper(client: Client, stored_user: StoredUser) -> None:
    password_user_credentials = client.users.reset_user_credential(
        stored_user.id,
        ResetUserCredentialAction(credential_type=CredentialType.password),
    )
    cli_print.log_info(f"Password reset for user with email '{stored_user.email}'.")
    cli_print.log_info(
        f"New password: {password_user_credentials.value.get_secret_value()}"
    )


def _set_user_status(client: Client, user_email: str, enabled: bool) -> None:
    stored_user = client.users.update_user_status_by_email(user_email, enabled)
    new_stauts = "enabled" if stored_user.enabled else "disabled"
    cli_print.log_info(f"Successfully {new_stauts} user with email '{user_email}'.")


def update_single_user(
    client: Client,
    stored_user: StoredUser,
    user: User,
    verbosity: cli_print.Verbosity = "high",
) -> StoredUser:
    return update_single_entity(
        pretty_entity_name=PRETTY_ENTITY_NAME,
        update_fn=lambda: client.users.update_user(stored_user.id, user),
        entity_identifier_value=stored_user.email,
        entity_identifier_type="email",
        verbosity=verbosity,
    )


def create_single_user(
    client: Client, user: User, verbosity: cli_print.Verbosity = "high"
) -> StoredUser:
    return create_single_entity(
        pretty_entity_name=PRETTY_ENTITY_NAME,
        create_fn=lambda: client.users.create_user(user),
        entity_identifier_value=user.email,
        entity_identifier_type="email",
        verbosity=verbosity,
    )
