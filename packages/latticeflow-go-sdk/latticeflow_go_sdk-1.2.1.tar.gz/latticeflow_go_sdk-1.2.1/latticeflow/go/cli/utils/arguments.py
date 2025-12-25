from __future__ import annotations

from pathlib import Path
from typing import Any

import typer

from latticeflow.go.models import Role


def parse_user_roles(roles: str) -> list[Role]:
    try:
        return [Role(value=role.strip()) for role in roles.split(",")]
    except Exception as error:
        raise typer.BadParameter(f"Could not parse roles '{roles}': {error}")


def check_path_not_emtpy(path: Path) -> Path:
    if not str(path).strip() or str(path) == ".":
        raise typer.BadParameter(f"Invalid path '{path}' provided.")
    return path


def single_config_path_argument(entity_name: str) -> Any:
    return typer.Argument(
        ...,
        help=f"Path to a single {entity_name} config.",
        callback=check_path_not_emtpy,
    )


def delete_key_argument(entity_name: str) -> Any:
    return typer.Argument(..., help=f"Key of the {entity_name} to be deleted.")


def export_key_argument(entity_name: str) -> Any:
    return typer.Argument(..., help=f"Key of the {entity_name} to be exported.")


def test_configuration_key_argument(entity_name: str) -> Any:
    return typer.Argument(
        ..., help=f"Key of the {entity_name} of which configuration should be tested."
    )


def glob_config_path_option(entity_name: str, *, is_required: bool = True) -> Any:
    return typer.Option(
        ... if is_required else None,
        "--file",
        "-f",
        help=f"Glob path to {entity_name} definitions.",
        callback=check_path_not_emtpy,
    )


json_flag_option = typer.Option(
    False, "-j", "--json", help="If set, the output is printed to stdout as JSON."
)


def should_list_all_option(entity_name: str) -> Any:
    return typer.Option(
        False,
        "-a",
        "--all",
        help=f"If set, all {entity_name} entities, including the user-created and "
        "the provided ones, are listed.",
    )


export_output_path_option = typer.Option(
    None,
    "-o",
    "--output",
    help="Path to output YAML file. Omit to print as JSON to stdout.",
    callback=check_path_not_emtpy,
)
create_user_email_option = typer.Option(
    ..., help="A unique email for the user. Example: 'johndoe@latticeflow.ai'."
)
create_user_name_option = typer.Option(
    ..., help="Name of the user. Example: 'John Doe'."
)
create_user_roles_option = typer.Option(
    ...,
    help=(
        "Role(s) to assign to the user (comma-separated). Possible values are: "
        "'admin', 'member', 'viewer'. Example:'admin,member'."
    ),
)
reset_password_email_option = typer.Option(
    ...,
    help="Email of the user whose password to reset. Example: 'johndoe@latticeflow.ai'.",
)
should_validate_only_option = typer.Option(
    False,
    "-v",
    "--validate",
    help="Whether to only validate the config file without creating or updating any entities.",
)
