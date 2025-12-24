from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.v1_model_get_model_by_id_body import V1ModelGetModelByIdBody
from ...models.v1_model_get_model_by_id_response_200 import (
    V1ModelGetModelByIdResponse200,
)
from ...models.v1_model_get_model_by_id_response_400 import (
    V1ModelGetModelByIdResponse400,
)
from ...models.v1_model_get_model_by_id_response_401 import (
    V1ModelGetModelByIdResponse401,
)
from ...models.v1_model_get_model_by_id_response_500 import (
    V1ModelGetModelByIdResponse500,
)
from ...types import Response


def _get_kwargs(
    *,
    body: V1ModelGetModelByIdBody,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/v1/api/models/get_by_id",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[
    Union[
        V1ModelGetModelByIdResponse200,
        V1ModelGetModelByIdResponse400,
        V1ModelGetModelByIdResponse401,
        V1ModelGetModelByIdResponse500,
    ]
]:
    if response.status_code == 200:
        response_200 = V1ModelGetModelByIdResponse200.from_dict(response.json())

        return response_200

    if response.status_code == 400:
        response_400 = V1ModelGetModelByIdResponse400.from_dict(response.json())

        return response_400

    if response.status_code == 401:
        response_401 = V1ModelGetModelByIdResponse401.from_dict(response.json())

        return response_401

    if response.status_code == 500:
        response_500 = V1ModelGetModelByIdResponse500.from_dict(response.json())

        return response_500

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[
    Union[
        V1ModelGetModelByIdResponse200,
        V1ModelGetModelByIdResponse400,
        V1ModelGetModelByIdResponse401,
        V1ModelGetModelByIdResponse500,
    ]
]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: V1ModelGetModelByIdBody,
) -> Response[
    Union[
        V1ModelGetModelByIdResponse200,
        V1ModelGetModelByIdResponse400,
        V1ModelGetModelByIdResponse401,
        V1ModelGetModelByIdResponse500,
    ]
]:
    """Retrieve a Model by it's primary id.

     Retrieve a model by it's primary id.

    Args:
        body (V1ModelGetModelByIdBody):  The Request body for /models/get_by_id

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[V1ModelGetModelByIdResponse200, V1ModelGetModelByIdResponse400, V1ModelGetModelByIdResponse401, V1ModelGetModelByIdResponse500]]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: Union[AuthenticatedClient, Client],
    body: V1ModelGetModelByIdBody,
) -> Optional[
    Union[
        V1ModelGetModelByIdResponse200,
        V1ModelGetModelByIdResponse400,
        V1ModelGetModelByIdResponse401,
        V1ModelGetModelByIdResponse500,
    ]
]:
    """Retrieve a Model by it's primary id.

     Retrieve a model by it's primary id.

    Args:
        body (V1ModelGetModelByIdBody):  The Request body for /models/get_by_id

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[V1ModelGetModelByIdResponse200, V1ModelGetModelByIdResponse400, V1ModelGetModelByIdResponse401, V1ModelGetModelByIdResponse500]
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: V1ModelGetModelByIdBody,
) -> Response[
    Union[
        V1ModelGetModelByIdResponse200,
        V1ModelGetModelByIdResponse400,
        V1ModelGetModelByIdResponse401,
        V1ModelGetModelByIdResponse500,
    ]
]:
    """Retrieve a Model by it's primary id.

     Retrieve a model by it's primary id.

    Args:
        body (V1ModelGetModelByIdBody):  The Request body for /models/get_by_id

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[V1ModelGetModelByIdResponse200, V1ModelGetModelByIdResponse400, V1ModelGetModelByIdResponse401, V1ModelGetModelByIdResponse500]]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    body: V1ModelGetModelByIdBody,
) -> Optional[
    Union[
        V1ModelGetModelByIdResponse200,
        V1ModelGetModelByIdResponse400,
        V1ModelGetModelByIdResponse401,
        V1ModelGetModelByIdResponse500,
    ]
]:
    """Retrieve a Model by it's primary id.

     Retrieve a model by it's primary id.

    Args:
        body (V1ModelGetModelByIdBody):  The Request body for /models/get_by_id

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[V1ModelGetModelByIdResponse200, V1ModelGetModelByIdResponse400, V1ModelGetModelByIdResponse401, V1ModelGetModelByIdResponse500]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
