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
from ...models.body import UpdateDatasetDataBody
from ...models.model import Error
from ...models.model import StoredDataset
from ...types import Response
from ...types import SDKVersionMismatchError


def _get_kwargs(dataset_id: str, body: UpdateDatasetDataBody) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {"method": "put", "url": f"/datasets/{dataset_id}/data"}

    _kwargs["files"] = body.to_multipart()

    if headers:
        _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Union[Error, StoredDataset]:
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
        response_200 = StoredDataset.model_validate(response.json())

        return response_200

    if response.status_code == 401:
        response_401 = Error.model_validate(response.json())

        return response_401

    if response.status_code == 404:
        response_404 = Error.model_validate(response.json())

        return response_404

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
) -> Response[Union[Error, StoredDataset]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    dataset_id: str,
    body: UpdateDatasetDataBody,
    *,
    client: Union[AuthenticatedClient, Client],
) -> Response[Union[Error, StoredDataset]]:
    """Update a dataset's data.

    Args:
        dataset_id (str):
        body (UpdateDatasetDataBody):

    Raises:
        errors.ErrorParsingException: If the server returns an unparseable entity instead of an ``Error``.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Error, StoredDataset]]
    """
    kwargs = _get_kwargs(dataset_id=dataset_id, body=body)

    response = client.get_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


def sync(
    dataset_id: str,
    body: UpdateDatasetDataBody,
    *,
    client: Union[AuthenticatedClient, Client],
) -> Union[Error, StoredDataset]:
    """Update a dataset's data.

    Args:
        dataset_id (str):
        body (UpdateDatasetDataBody):

    Raises:
        errors.ErrorParsingException: If the server returns an unparseable entity instead of an ``Error``.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Error, StoredDataset]
    """
    return sync_detailed(dataset_id=dataset_id, client=client, body=body).parsed


async def asyncio_detailed(
    dataset_id: str,
    body: UpdateDatasetDataBody,
    *,
    client: Union[AuthenticatedClient, Client],
) -> Response[Union[Error, StoredDataset]]:
    """Update a dataset's data.

    Args:
        dataset_id (str):
        body (UpdateDatasetDataBody):

    Raises:
        errors.ErrorParsingException: If the server returns an unparseable entity instead of an ``Error``.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Error, StoredDataset]]
    """
    kwargs = _get_kwargs(dataset_id=dataset_id, body=body)

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    dataset_id: str,
    body: UpdateDatasetDataBody,
    *,
    client: Union[AuthenticatedClient, Client],
) -> Union[Error, StoredDataset]:
    """Update a dataset's data.

    Args:
        dataset_id (str):
        body (UpdateDatasetDataBody):

    Raises:
        errors.ErrorParsingException: If the server returns an unparseable entity instead of an ``Error``.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Error, StoredDataset]
    """
    return (
        await asyncio_detailed(dataset_id=dataset_id, client=client, body=body)
    ).parsed
