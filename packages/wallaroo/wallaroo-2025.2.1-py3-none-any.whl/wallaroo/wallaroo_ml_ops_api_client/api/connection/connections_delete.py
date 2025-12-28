from http import HTTPStatus
from typing import Any, Optional, Union, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.connections_delete_body import ConnectionsDeleteBody
from ...models.connections_delete_response_400 import ConnectionsDeleteResponse400
from ...models.connections_delete_response_401 import ConnectionsDeleteResponse401
from ...models.connections_delete_response_500 import ConnectionsDeleteResponse500
from ...types import Response


def _get_kwargs(
    *,
    body: ConnectionsDeleteBody,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/v1/api/connections/delete",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[
    Union[
        Any,
        ConnectionsDeleteResponse400,
        ConnectionsDeleteResponse401,
        ConnectionsDeleteResponse500,
    ]
]:
    if response.status_code == 204:
        response_204 = cast(Any, None)
        return response_204

    if response.status_code == 400:
        response_400 = ConnectionsDeleteResponse400.from_dict(response.json())

        return response_400

    if response.status_code == 401:
        response_401 = ConnectionsDeleteResponse401.from_dict(response.json())

        return response_401

    if response.status_code == 500:
        response_500 = ConnectionsDeleteResponse500.from_dict(response.json())

        return response_500

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[
    Union[
        Any,
        ConnectionsDeleteResponse400,
        ConnectionsDeleteResponse401,
        ConnectionsDeleteResponse500,
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
    body: ConnectionsDeleteBody,
) -> Response[
    Union[
        Any,
        ConnectionsDeleteResponse400,
        ConnectionsDeleteResponse401,
        ConnectionsDeleteResponse500,
    ]
]:
    """Delete a connection

     Delete a connection

    Args:
        body (ConnectionsDeleteBody):  Request to delete a Connection

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Any, ConnectionsDeleteResponse400, ConnectionsDeleteResponse401, ConnectionsDeleteResponse500]]
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
    body: ConnectionsDeleteBody,
) -> Optional[
    Union[
        Any,
        ConnectionsDeleteResponse400,
        ConnectionsDeleteResponse401,
        ConnectionsDeleteResponse500,
    ]
]:
    """Delete a connection

     Delete a connection

    Args:
        body (ConnectionsDeleteBody):  Request to delete a Connection

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Any, ConnectionsDeleteResponse400, ConnectionsDeleteResponse401, ConnectionsDeleteResponse500]
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: ConnectionsDeleteBody,
) -> Response[
    Union[
        Any,
        ConnectionsDeleteResponse400,
        ConnectionsDeleteResponse401,
        ConnectionsDeleteResponse500,
    ]
]:
    """Delete a connection

     Delete a connection

    Args:
        body (ConnectionsDeleteBody):  Request to delete a Connection

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Any, ConnectionsDeleteResponse400, ConnectionsDeleteResponse401, ConnectionsDeleteResponse500]]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    body: ConnectionsDeleteBody,
) -> Optional[
    Union[
        Any,
        ConnectionsDeleteResponse400,
        ConnectionsDeleteResponse401,
        ConnectionsDeleteResponse500,
    ]
]:
    """Delete a connection

     Delete a connection

    Args:
        body (ConnectionsDeleteBody):  Request to delete a Connection

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Any, ConnectionsDeleteResponse400, ConnectionsDeleteResponse401, ConnectionsDeleteResponse500]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
