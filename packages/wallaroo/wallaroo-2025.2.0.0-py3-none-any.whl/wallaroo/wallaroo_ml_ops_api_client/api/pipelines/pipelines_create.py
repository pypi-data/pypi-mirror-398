from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.pipelines_create_body import PipelinesCreateBody
from ...models.pipelines_create_response_200 import PipelinesCreateResponse200
from ...models.pipelines_create_response_400 import PipelinesCreateResponse400
from ...models.pipelines_create_response_401 import PipelinesCreateResponse401
from ...models.pipelines_create_response_500 import PipelinesCreateResponse500
from ...types import Response


def _get_kwargs(
    *,
    body: PipelinesCreateBody,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/v1/api/pipelines/create",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[
    Union[
        PipelinesCreateResponse200,
        PipelinesCreateResponse400,
        PipelinesCreateResponse401,
        PipelinesCreateResponse500,
    ]
]:
    if response.status_code == 200:
        response_200 = PipelinesCreateResponse200.from_dict(response.json())

        return response_200

    if response.status_code == 400:
        response_400 = PipelinesCreateResponse400.from_dict(response.json())

        return response_400

    if response.status_code == 401:
        response_401 = PipelinesCreateResponse401.from_dict(response.json())

        return response_401

    if response.status_code == 500:
        response_500 = PipelinesCreateResponse500.from_dict(response.json())

        return response_500

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[
    Union[
        PipelinesCreateResponse200,
        PipelinesCreateResponse400,
        PipelinesCreateResponse401,
        PipelinesCreateResponse500,
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
    body: PipelinesCreateBody,
) -> Response[
    Union[
        PipelinesCreateResponse200,
        PipelinesCreateResponse400,
        PipelinesCreateResponse401,
        PipelinesCreateResponse500,
    ]
]:
    """Create a new pipeline

     Creates a new pipeline.

    Args:
        body (PipelinesCreateBody):  Request to create a new pipeline in a workspace.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[PipelinesCreateResponse200, PipelinesCreateResponse400, PipelinesCreateResponse401, PipelinesCreateResponse500]]
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
    body: PipelinesCreateBody,
) -> Optional[
    Union[
        PipelinesCreateResponse200,
        PipelinesCreateResponse400,
        PipelinesCreateResponse401,
        PipelinesCreateResponse500,
    ]
]:
    """Create a new pipeline

     Creates a new pipeline.

    Args:
        body (PipelinesCreateBody):  Request to create a new pipeline in a workspace.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[PipelinesCreateResponse200, PipelinesCreateResponse400, PipelinesCreateResponse401, PipelinesCreateResponse500]
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: PipelinesCreateBody,
) -> Response[
    Union[
        PipelinesCreateResponse200,
        PipelinesCreateResponse400,
        PipelinesCreateResponse401,
        PipelinesCreateResponse500,
    ]
]:
    """Create a new pipeline

     Creates a new pipeline.

    Args:
        body (PipelinesCreateBody):  Request to create a new pipeline in a workspace.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[PipelinesCreateResponse200, PipelinesCreateResponse400, PipelinesCreateResponse401, PipelinesCreateResponse500]]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    body: PipelinesCreateBody,
) -> Optional[
    Union[
        PipelinesCreateResponse200,
        PipelinesCreateResponse400,
        PipelinesCreateResponse401,
        PipelinesCreateResponse500,
    ]
]:
    """Create a new pipeline

     Creates a new pipeline.

    Args:
        body (PipelinesCreateBody):  Request to create a new pipeline in a workspace.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[PipelinesCreateResponse200, PipelinesCreateResponse400, PipelinesCreateResponse401, PipelinesCreateResponse500]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
