from __future__ import annotations

import os
import string
from pathlib import Path
from typing import Any
from typing import TYPE_CHECKING

import yaml

from latticeflow.go.cli.utils.dtypes import ResolvedData
from latticeflow.go.utils.resolution import load_recursively
from latticeflow.go.utils.resolution import YAMLOriginInfo


if TYPE_CHECKING:
    from _typeshed import SupportsRead  # Type used by `yaml.load`.


def _include_constructor(loader: YAMLLoader, node: yaml.nodes.ScalarNode) -> str:
    """Copies the text contents of a file in place of '!include <file>'."""
    include_relative_path = Path(loader.construct_scalar(node))

    include_path = loader._root / include_relative_path
    if not include_path.exists():
        raise FileNotFoundError(
            f"Included file with '!include' directive does not exist at "
            f"'{include_relative_path}'. Make sure that the path is relative to the "
            f"root file '{loader.name}'."
        )

    # Strip whitespace to allow for empty lines at the begging or the end of the file.
    return include_path.read_text().strip()


def _has_unexpanded_var(value: str) -> bool:
    if value == "$ref":
        return False
    return value.startswith("$") and all(w not in value for w in string.whitespace)


def _expandvars_constructor(loader: YAMLLoader, node: yaml.nodes.ScalarNode) -> str:
    """Expands every string starting with '$VAR' or '${VAR}' with its environment
    variable value.

    If the variable is not set, the string is left unchanged. It follows similar
    behavior to ``os.path.expandvars``.

    Variables are expanded only if they are the only thing in the string.

    Examples:
        If we set the environment variables ``LF_TEST_VAR=secret`` and
        ``MY_MODEL=my-model`` and the input YAML is:

        ```yaml
        description: This model uses env var $LF_TEST_VAR.
        config:
            api_key: $LF_TEST_VAR
            model_key: $MY_MODEL
        ```

        The loaded dictionary will then be:

        ```python
        {
            "description": "This model uses env var $LF_TEST_VAR.",
            "config": {"api_key": "secret", "model_key": "my-model"},
        }
        ```
    """
    value: str = yaml.SafeLoader.construct_scalar(loader, node)
    if _should_expand_env_vars(loader._key_path, value):
        expanded = os.path.expandvars(value)
        if _has_unexpanded_var(expanded):
            # import here to avoid circular import.
            from latticeflow.go.cli.utils import printing

            printing.log_warning(
                f"Input at path '{loader._key_path}' specifies an environment "
                f"variable that is not set: '{value}'."
            )
        return expanded
    return value


def _should_expand_env_vars(key_path: list[str], value: str) -> bool:
    """Function that decides if environment variables in the current value should be expanded."""
    return len(key_path) > 0 and _has_unexpanded_var(value)


class YAMLLoader(yaml.SafeLoader):
    def __init__(self, stream: Any) -> None:
        self._root = Path(getattr(stream, "name", ".")).resolve().parent

        # Constructs a list representing the path of the node in the YAML.
        # Example:
        #   config:
        #     api_key: $VAR
        # The `_key_path` for '$VAR' node will resolve to `['config', 'api_key']`.
        self._key_path: list[str] = []
        super().__init__(stream)

    def construct_mapping(
        self, node: yaml.nodes.MappingNode, deep: bool = False
    ) -> dict:
        if isinstance(node, yaml.MappingNode):
            # Keep `SafeLoader` behavior (handles aliases, merges, etc.).
            self.flatten_mapping(node)

        mapping: dict[Any, Any] = {}
        for key_node, value_node in node.value:
            # Examples:
            # `key_node = ScalarNode(tag='tag:yaml.org,2002:str', value='api_key')`
            # `value_node = ScalarNode(tag='tag:yaml.org,2002:str', value='$VAR')`
            key = self.construct_object(key_node, deep=deep)
            self._key_path.append(str(key))
            try:
                value = self.construct_object(value_node, deep=deep)
            finally:
                # We pop to return to the previous node.
                self._key_path.pop()

            if key in mapping:
                raise ValueError(f"Duplicate key '{key!r}' key found in YAML.")
            mapping[key] = value

        return mapping


# We have to register the additional constructors like this (the intended way) instead
# of overwriting the yaml_constructors dict directly, as otherwise parsing of other
# types breaks.
YAMLLoader.add_constructor("!include", _include_constructor)
# Overrides the default string constructor to expand env vars.
YAMLLoader.add_constructor("tag:yaml.org,2002:str", _expandvars_constructor)


def load_yaml(stream: str | bytes | SupportsRead[str] | SupportsRead[bytes]) -> Any:
    return yaml.load(stream, Loader=YAMLLoader)  # nosec B506


def load_yaml_recursively(
    file_or_data: Path | ResolvedData,
) -> tuple[dict, YAMLOriginInfo]:
    if isinstance(file_or_data, Path):
        with open(file_or_data, "r") as f:
            loaded_yaml = load_yaml(f)
            return load_recursively(
                doc=loaded_yaml, doc_path=Path(file_or_data), yaml_loader=load_yaml
            )
    else:
        return load_recursively(
            doc=file_or_data.data, doc_path=file_or_data.path, yaml_loader=load_yaml
        )


class PrettySafeDumper(yaml.SafeDumper):
    pass


def long_str_representer(dumper: yaml.SafeDumper, value: str) -> yaml.nodes.ScalarNode:
    if "\n" in value:
        return dumper.represent_scalar("tag:yaml.org,2002:str", value, style="|")

    return yaml.SafeDumper.represent_str(dumper, value)


PrettySafeDumper.add_representer(str, long_str_representer)


def yaml_safe_dump_pretty(data: Any) -> str:
    """Serializes a Python object into a pretty YAML stream."""
    return yaml.dump(data, Dumper=PrettySafeDumper, sort_keys=False)
