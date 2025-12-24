from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.connections_list_body import ConnectionsListBody
from ...models.connections_list_response_200 import ConnectionsListResponse200
from ...models.connections_list_response_400 import ConnectionsListResponse400
from ...models.connections_list_response_401 import ConnectionsListResponse401
from ...models.connections_list_response_500 import ConnectionsListResponse500
from ...types import Response


def _get_kwargs(
    *,
    body: ConnectionsListBody,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/v1/api/connections/list",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[
    Union[
        ConnectionsListResponse200,
        ConnectionsListResponse400,
        ConnectionsListResponse401,
        ConnectionsListResponse500,
    ]
]:
    if response.status_code == 200:
        response_200 = ConnectionsListResponse200.from_dict(response.json())

        return response_200

    if response.status_code == 400:
        response_400 = ConnectionsListResponse400.from_dict(response.json())

        return response_400

    if response.status_code == 401:
        response_401 = ConnectionsListResponse401.from_dict(response.json())

        return response_401

    if response.status_code == 500:
        response_500 = ConnectionsListResponse500.from_dict(response.json())

        return response_500

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[
    Union[
        ConnectionsListResponse200,
        ConnectionsListResponse400,
        ConnectionsListResponse401,
        ConnectionsListResponse500,
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
    body: ConnectionsListBody,
) -> Response[
    Union[
        ConnectionsListResponse200,
        ConnectionsListResponse400,
        ConnectionsListResponse401,
        ConnectionsListResponse500,
    ]
]:
    """List all connections

     List Connections

    Args:
        body (ConnectionsListBody):  Request to list Connections

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[ConnectionsListResponse200, ConnectionsListResponse400, ConnectionsListResponse401, ConnectionsListResponse500]]
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
    body: ConnectionsListBody,
) -> Optional[
    Union[
        ConnectionsListResponse200,
        ConnectionsListResponse400,
        ConnectionsListResponse401,
        ConnectionsListResponse500,
    ]
]:
    """List all connections

     List Connections

    Args:
        body (ConnectionsListBody):  Request to list Connections

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[ConnectionsListResponse200, ConnectionsListResponse400, ConnectionsListResponse401, ConnectionsListResponse500]
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: ConnectionsListBody,
) -> Response[
    Union[
        ConnectionsListResponse200,
        ConnectionsListResponse400,
        ConnectionsListResponse401,
        ConnectionsListResponse500,
    ]
]:
    """List all connections

     List Connections

    Args:
        body (ConnectionsListBody):  Request to list Connections

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[ConnectionsListResponse200, ConnectionsListResponse400, ConnectionsListResponse401, ConnectionsListResponse500]]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    body: ConnectionsListBody,
) -> Optional[
    Union[
        ConnectionsListResponse200,
        ConnectionsListResponse400,
        ConnectionsListResponse401,
        ConnectionsListResponse500,
    ]
]:
    """List all connections

     List Connections

    Args:
        body (ConnectionsListBody):  Request to list Connections

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[ConnectionsListResponse200, ConnectionsListResponse400, ConnectionsListResponse401, ConnectionsListResponse500]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
