from __future__ import annotations

import functools
import inspect
from typing import Any
from typing import Callable
from typing import cast

import typer


def with_callback(
    cb: Callable[[], None],
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def deco(fn: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(fn)
        def wrapped(*args: Any, **kwargs: Any) -> Any:
            cb()
            return fn(*args, **kwargs)

        cast(Any, wrapped).__signature__ = inspect.signature(fn)
        return wrapped

    return deco


def register_shorthand_list_command(
    app: typer.Typer,
    command_name: str,
    command: Callable[..., None],
    entity_name_plural: str,
    subapp_name: str,
) -> None:
    app.command(
        command_name,
        short_help=f"List all {entity_name_plural} as JSON or in a table. Shorthand for `lf {subapp_name} list`.",
    )(command)
