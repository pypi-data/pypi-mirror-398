# Based on our override (see README.md) of openapi-python-client's Jinja template
# (https://github.com/openapi-generators/openapi-python-client/blob/main/openapi_python_client/templates/types.py.jinja)
# Does not match the original logic, as our version follows Pydantic v2 standards
from __future__ import annotations

import io
from collections.abc import Mapping
from collections.abc import MutableMapping
from http import HTTPStatus
from typing import Any
from typing import Generic
from typing import IO
from typing import Optional
from typing import TypeVar
from typing import Union

from pydantic_core import core_schema

from latticeflow.go.utils.constants import SDK_PACKAGE_NAME

from .models.base_model import LFBaseModel
from .models.model import Error


class ApiError(Exception):
    def __init__(self, error: Error) -> None:
        self.error = error

    def __str__(self) -> str:
        return f"{self.error}"


class SDKVersionMismatchError(Exception):
    def __init__(self, *, api_version: str, client_version: str) -> None:
        self.api_version = api_version
        self.client_version = client_version

    def __str__(self) -> str:
        return (
            f"The SDK version '{self.client_version}' does not match the API "
            f"version '{self.api_version}'. Update your SDK package to the correct "
            f"version using `uv pip install {SDK_PACKAGE_NAME}={self.api_version}`"
            " to resolve the issue."
        )


class Unset:
    """Marker type for 'not provided'."""

    def __bool__(self) -> bool:
        return False

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: Any
    ) -> core_schema.CoreSchema:
        # Pretend it's always valid, represented as None in schema
        return core_schema.no_info_plain_validator_function(lambda _: UNSET)

    @classmethod
    def __get_pydantic_json_schema__(
        cls, core_schema: core_schema.CoreSchema, handler: Any
    ) -> dict[str, Any]:
        # Show up as 'null' in generated OpenAPI
        return {"type": "null", "description": "Unset sentinel"}


UNSET: Unset = Unset()


# The types that `httpx.Client(files=)` can accept, copied from that library.
FileContent = Union[IO[bytes], bytes, str]
FileTypes = Union[
    # (filename, file (or bytes), content_type)
    tuple[Optional[str], FileContent, Optional[str]],
    # (filename, file (or bytes), content_type, headers)
    tuple[Optional[str], FileContent, Optional[str], Mapping[str, str]],
]
RequestFiles = list[tuple[str, FileTypes]]


class File(LFBaseModel):
    """Contains information for file uploads."""

    payload: io.BytesIO
    file_name: Optional[str] = None
    mime_type: Optional[str] = None

    def to_tuple(self) -> FileTypes:
        """Return a tuple representation that httpx will accept for multipart/form-data."""
        return self.file_name, self.payload, self.mime_type

    model_config = {"arbitrary_types_allowed": True}


T = TypeVar("T")


class Response(LFBaseModel, Generic[T]):
    """A response from an endpoint"""

    status_code: HTTPStatus
    content: bytes
    headers: MutableMapping[str, str]
    parsed: T


__all__ = ["UNSET", "File", "FileTypes", "RequestFiles", "Response", "Unset"]
