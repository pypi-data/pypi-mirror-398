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
from ...models.model import ModelAdapterInput
from ...models.model import RawModelInput
from ...types import Response
from ...types import SDKVersionMismatchError


def _get_kwargs(model_id: str, body: ModelAdapterInput) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": f"/models/{model_id}/transform-input",
    }

    _kwargs["json"] = body.model_dump(mode="json")

    headers["Content-Type"] = "application/json"

    if headers:
        _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Union[Error, RawModelInput]:
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
        response_200 = RawModelInput.model_validate(response.json())

        return response_200

    if response.status_code == 401:
        response_401 = Error.model_validate(response.json())

        return response_401

    if response.status_code == 404:
        response_404 = Error.model_validate(response.json())

        return response_404

    if response.status_code == 422:
        response_422 = Error.model_validate(response.json())

        return response_422

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
) -> Response[Union[Error, RawModelInput]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    model_id: str,
    body: ModelAdapterInput,
    *,
    client: Union[AuthenticatedClient, Client],
) -> Response[Union[Error, RawModelInput]]:
    """Transforms the given input so it is suitable for use with a model.

     This API attempts to transform a model input formatted in the AIGO format to
    the format required by the model using a model adapter.

    This API is intended to be used for probing the correctness of the model adapter.

    Nothing is sent to the model in the process.

    Args:
        model_id (str):
        body (ModelAdapterInput): Model input represented in the LatticeFlow AIGO format.

    Raises:
        errors.ErrorParsingException: If the server returns an unparseable entity instead of an ``Error``.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Error, RawModelInput]]
    """
    kwargs = _get_kwargs(model_id=model_id, body=body)

    response = client.get_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


def sync(
    model_id: str,
    body: ModelAdapterInput,
    *,
    client: Union[AuthenticatedClient, Client],
) -> Union[Error, RawModelInput]:
    """Transforms the given input so it is suitable for use with a model.

     This API attempts to transform a model input formatted in the AIGO format to
    the format required by the model using a model adapter.

    This API is intended to be used for probing the correctness of the model adapter.

    Nothing is sent to the model in the process.

    Args:
        model_id (str):
        body (ModelAdapterInput): Model input represented in the LatticeFlow AIGO format.

    Raises:
        errors.ErrorParsingException: If the server returns an unparseable entity instead of an ``Error``.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Error, RawModelInput]
    """
    return sync_detailed(model_id=model_id, client=client, body=body).parsed


async def asyncio_detailed(
    model_id: str,
    body: ModelAdapterInput,
    *,
    client: Union[AuthenticatedClient, Client],
) -> Response[Union[Error, RawModelInput]]:
    """Transforms the given input so it is suitable for use with a model.

     This API attempts to transform a model input formatted in the AIGO format to
    the format required by the model using a model adapter.

    This API is intended to be used for probing the correctness of the model adapter.

    Nothing is sent to the model in the process.

    Args:
        model_id (str):
        body (ModelAdapterInput): Model input represented in the LatticeFlow AIGO format.

    Raises:
        errors.ErrorParsingException: If the server returns an unparseable entity instead of an ``Error``.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Error, RawModelInput]]
    """
    kwargs = _get_kwargs(model_id=model_id, body=body)

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    model_id: str,
    body: ModelAdapterInput,
    *,
    client: Union[AuthenticatedClient, Client],
) -> Union[Error, RawModelInput]:
    """Transforms the given input so it is suitable for use with a model.

     This API attempts to transform a model input formatted in the AIGO format to
    the format required by the model using a model adapter.

    This API is intended to be used for probing the correctness of the model adapter.

    Nothing is sent to the model in the process.

    Args:
        model_id (str):
        body (ModelAdapterInput): Model input represented in the LatticeFlow AIGO format.

    Raises:
        errors.ErrorParsingException: If the server returns an unparseable entity instead of an ``Error``.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Error, RawModelInput]
    """
    return (await asyncio_detailed(model_id=model_id, client=client, body=body)).parsed
