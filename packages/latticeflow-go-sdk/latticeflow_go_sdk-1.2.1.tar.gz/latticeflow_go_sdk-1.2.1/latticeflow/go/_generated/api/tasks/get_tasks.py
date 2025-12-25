# Based on our override (see README.md) of openapi-python-client's Jinja template
# (https://github.com/openapi-generators/openapi-python-client/blob/main/openapi_python_client/templates/endpoint_module.py.jinja)
from __future__ import annotations

from http import HTTPStatus
from typing import Any
from typing import Union

import httpx
from pydantic import ValidationError

from ... import errors
from ...client import AuthenticatedClient
from ...client import Client
from ...models.model import Error
from ...models.model import StoredTasks
from ...types import Response
from ...types import SDKVersionMismatchError
from ...types import UNSET
from ...types import Unset


def _get_kwargs(
    *, key: Union[Unset, str] = UNSET, user_only: Union[Unset, bool] = False
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["key"] = key

    params["user_only"] = user_only

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {"method": "get", "url": "/tasks", "params": params}

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Union[Error, StoredTasks]:
    # NOTE: If we see the status code is 426, it means there is a version mismatch beteween the SDK
    # and the API. In such case we want to handle this error in special way - raise it. This code was
    # added by the Jinja template located at `templates/overrides/endpoint_module.py.jinja`.
    if response.status_code == 426:
        version_mismatch_error_dict = response.json()
        raise SDKVersionMismatchError(
            api_version=version_mismatch_error_dict["api_version"],
            client_version=version_mismatch_error_dict["client_version"],
        )

    if response.status_code == 200:
        response_200 = StoredTasks.model_validate(response.json())

        return response_200

    if response.status_code == 401:
        response_401 = Error.model_validate(response.json())

        return response_401

    # NOTE: We always try to parse the response as an error if all previous parsing has failed,
    # because the client generator only adds handling for status codes defined in the OpenAPI spec,
    # which does not always cover all possible error codes. This code was added by the Jinja template
    # located at `templates/overrides/endpoint_module.py.jinja`.
    try:
        return Error.model_validate(response.json())
    except ValidationError as e:
        raise errors.ErrorParsingException(
            "Could not parse the API-returned object as `Error`", e
        )


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[Union[Error, StoredTasks]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    key: Union[Unset, str] = UNSET,
    user_only: Union[Unset, bool] = False,
) -> Response[Union[Error, StoredTasks]]:
    """Get all tasks

    Args:
        key (Union[Unset, str]):
        user_only (Union[Unset, bool]):  Default: False.

    Raises:
        errors.ErrorParsingException: If the server returns an unparseable entity instead of an ``Error``.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Error, StoredTasks]]
    """
    kwargs = _get_kwargs(key=key, user_only=user_only)

    response = client.get_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


def sync(
    *,
    client: Union[AuthenticatedClient, Client],
    key: Union[Unset, str] = UNSET,
    user_only: Union[Unset, bool] = False,
) -> Union[Error, StoredTasks]:
    """Get all tasks

    Args:
        key (Union[Unset, str]):
        user_only (Union[Unset, bool]):  Default: False.

    Raises:
        errors.ErrorParsingException: If the server returns an unparseable entity instead of an ``Error``.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Error, StoredTasks]
    """
    return sync_detailed(client=client, key=key, user_only=user_only).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    key: Union[Unset, str] = UNSET,
    user_only: Union[Unset, bool] = False,
) -> Response[Union[Error, StoredTasks]]:
    """Get all tasks

    Args:
        key (Union[Unset, str]):
        user_only (Union[Unset, bool]):  Default: False.

    Raises:
        errors.ErrorParsingException: If the server returns an unparseable entity instead of an ``Error``.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Error, StoredTasks]]
    """
    kwargs = _get_kwargs(key=key, user_only=user_only)

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    key: Union[Unset, str] = UNSET,
    user_only: Union[Unset, bool] = False,
) -> Union[Error, StoredTasks]:
    """Get all tasks

    Args:
        key (Union[Unset, str]):
        user_only (Union[Unset, bool]):  Default: False.

    Raises:
        errors.ErrorParsingException: If the server returns an unparseable entity instead of an ``Error``.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Error, StoredTasks]
    """
    return (await asyncio_detailed(client=client, key=key, user_only=user_only)).parsed
