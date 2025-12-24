from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.connections_get_body import ConnectionsGetBody
from ...models.connections_get_response_200 import ConnectionsGetResponse200
from ...models.connections_get_response_400 import ConnectionsGetResponse400
from ...models.connections_get_response_401 import ConnectionsGetResponse401
from ...models.connections_get_response_404 import ConnectionsGetResponse404
from ...models.connections_get_response_500 import ConnectionsGetResponse500
from ...types import Response


def _get_kwargs(
    *,
    body: ConnectionsGetBody,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/v1/api/connections/get",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[
    Union[
        ConnectionsGetResponse200,
        ConnectionsGetResponse400,
        ConnectionsGetResponse401,
        ConnectionsGetResponse404,
        ConnectionsGetResponse500,
    ]
]:
    if response.status_code == 200:
        response_200 = ConnectionsGetResponse200.from_dict(response.json())

        return response_200

    if response.status_code == 400:
        response_400 = ConnectionsGetResponse400.from_dict(response.json())

        return response_400

    if response.status_code == 401:
        response_401 = ConnectionsGetResponse401.from_dict(response.json())

        return response_401

    if response.status_code == 404:
        response_404 = ConnectionsGetResponse404.from_dict(response.json())

        return response_404

    if response.status_code == 500:
        response_500 = ConnectionsGetResponse500.from_dict(response.json())

        return response_500

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[
    Union[
        ConnectionsGetResponse200,
        ConnectionsGetResponse400,
        ConnectionsGetResponse401,
        ConnectionsGetResponse404,
        ConnectionsGetResponse500,
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
    body: ConnectionsGetBody,
) -> Response[
    Union[
        ConnectionsGetResponse200,
        ConnectionsGetResponse400,
        ConnectionsGetResponse401,
        ConnectionsGetResponse404,
        ConnectionsGetResponse500,
    ]
]:
    """Get a connection

     Get a connection

    Args:
        body (ConnectionsGetBody):  Request to get a Connection

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[ConnectionsGetResponse200, ConnectionsGetResponse400, ConnectionsGetResponse401, ConnectionsGetResponse404, ConnectionsGetResponse500]]
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
    body: ConnectionsGetBody,
) -> Optional[
    Union[
        ConnectionsGetResponse200,
        ConnectionsGetResponse400,
        ConnectionsGetResponse401,
        ConnectionsGetResponse404,
        ConnectionsGetResponse500,
    ]
]:
    """Get a connection

     Get a connection

    Args:
        body (ConnectionsGetBody):  Request to get a Connection

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[ConnectionsGetResponse200, ConnectionsGetResponse400, ConnectionsGetResponse401, ConnectionsGetResponse404, ConnectionsGetResponse500]
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: ConnectionsGetBody,
) -> Response[
    Union[
        ConnectionsGetResponse200,
        ConnectionsGetResponse400,
        ConnectionsGetResponse401,
        ConnectionsGetResponse404,
        ConnectionsGetResponse500,
    ]
]:
    """Get a connection

     Get a connection

    Args:
        body (ConnectionsGetBody):  Request to get a Connection

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[ConnectionsGetResponse200, ConnectionsGetResponse400, ConnectionsGetResponse401, ConnectionsGetResponse404, ConnectionsGetResponse500]]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    body: ConnectionsGetBody,
) -> Optional[
    Union[
        ConnectionsGetResponse200,
        ConnectionsGetResponse400,
        ConnectionsGetResponse401,
        ConnectionsGetResponse404,
        ConnectionsGetResponse500,
    ]
]:
    """Get a connection

     Get a connection

    Args:
        body (ConnectionsGetBody):  Request to get a Connection

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[ConnectionsGetResponse200, ConnectionsGetResponse400, ConnectionsGetResponse401, ConnectionsGetResponse404, ConnectionsGetResponse500]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
