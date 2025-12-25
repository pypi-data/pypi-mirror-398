from __future__ import annotations

import re
from pathlib import Path
from typing import Any
from typing import Callable
from typing import Mapping
from typing import Union

import yaml


SCHEMA_REGEXP = re.compile("[A-Za-z]+://")

OriginData = Path | Mapping[Union[str, int], "OriginData"]


class YAMLOriginInfo:
    def __init__(self, root_file_path: Path, data: OriginData) -> None:
        self._root_file_path = root_file_path
        self._data = data

    @classmethod
    def merge(
        cls, root_file_path: Path, origin_infos: Mapping[str | int, YAMLOriginInfo]
    ) -> YAMLOriginInfo:
        data = {
            identifier: origin_info._data
            for identifier, origin_info in origin_infos.items()
        }
        return YAMLOriginInfo(root_file_path, data)

    def with_root(self, root_file_path: Path) -> YAMLOriginInfo:
        return YAMLOriginInfo(root_file_path, self._data)

    def get(self, identifier: str | int) -> YAMLOriginInfo:
        if isinstance(self._data, Path):
            raise ValueError("Cannot traverse YAML origin info leaf node.")
        return YAMLOriginInfo(self._root_file_path, self._data[identifier])

    def get_root_file_path(self) -> Path:
        return self._root_file_path

    def get_file_path(self) -> Path:
        if not isinstance(self._data, Path):
            raise ValueError("YAML origin info is only available for leaf nodes.")
        return self._data


def resolve_value(
    value: str,
    doc_path: Path,
    loc: str,
    yaml_loader: Callable[[Any], Any] = yaml.safe_load,
) -> tuple[dict, YAMLOriginInfo]:
    if value.startswith("#"):
        raise NotImplementedError(
            "References relative to schema root (i.e. starting with #) are not supported."
        )
    if SCHEMA_REGEXP.match(value):
        raise NotImplementedError("Remote references are not supported.")

    # Local file reference
    if Path(value).is_absolute():
        local_file_path = Path(value)
    else:
        local_file_path = Path(doc_path).parent / value

    try:
        with local_file_path.open() as f:
            inner = yaml_loader(f)
            return load_recursively(
                doc=inner, doc_path=local_file_path, loc=loc, yaml_loader=yaml_loader
            )
    except FileNotFoundError as e:
        raise FileNotFoundError(f"Failed to resolve {loc}: {e}")


def load_recursively(
    doc: Any,
    doc_path: Path,
    loc: str = "",
    yaml_loader: Callable[[Any], Any] = yaml.safe_load,
) -> tuple[Any, YAMLOriginInfo]:
    if isinstance(doc, dict):
        loaded_ref_and_origin_info = None
        if "$ref" in doc:
            ref_value = doc.pop("$ref")
            loaded_ref_and_origin_info = resolve_value(
                ref_value, doc_path, loc, yaml_loader
            )

        loaded_doc: Any = {}
        doc_origin_infos: dict[str | int, YAMLOriginInfo] = {}
        for key, value in doc.items():
            loaded_value, value_origin_info = load_recursively(
                value,
                doc_path,
                loc=f"{loc}.{key}" if loc != "" else key,
                yaml_loader=yaml_loader,
            )
            loaded_doc[key] = loaded_value
            doc_origin_infos[key] = value_origin_info

        if loaded_ref_and_origin_info is None:
            return loaded_doc, YAMLOriginInfo.merge(doc_path, doc_origin_infos)

        loaded_ref, ref_origin_info = loaded_ref_and_origin_info
        if loaded_doc == {}:
            # Replace the full doc by the ref.
            return (loaded_ref, ref_origin_info.with_root(doc_path))
        elif isinstance(loaded_ref, dict):
            # Insert the ref into the doc.
            loaded_doc = {**loaded_doc, **loaded_ref}
            doc_origin_infos = {
                **doc_origin_infos,
                **{k: ref_origin_info.get(k) for k in loaded_ref},
            }
            return loaded_doc, YAMLOriginInfo.merge(doc_path, doc_origin_infos)
        else:
            prefix = f"Loading error for {loc}: " if loc != "" else ""

            raise ValueError(f"""{prefix}Cannot reference a non-dict value if other keys are present in the schema.
Referenced Value: {loaded_ref}
Schema: {doc | {"$ref": ref_value}}
""")
    elif isinstance(doc, list):
        loaded_doc = []
        doc_origin_infos = {}
        for i, value in enumerate(doc):
            loaded_value, value_origin_info = load_recursively(
                value, doc_path, loc=f"{loc}[{i}]", yaml_loader=yaml_loader
            )
            loaded_doc.append(loaded_value)
            doc_origin_infos[i] = value_origin_info
        return loaded_doc, YAMLOriginInfo.merge(doc_path, doc_origin_infos)
    else:
        return doc, YAMLOriginInfo(doc_path, doc_path)
