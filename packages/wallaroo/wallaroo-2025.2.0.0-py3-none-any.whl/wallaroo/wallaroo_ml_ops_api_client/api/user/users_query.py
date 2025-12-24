from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.users_query_body import UsersQueryBody
from ...models.users_query_response_200 import UsersQueryResponse200
from ...models.users_query_response_400 import UsersQueryResponse400
from ...models.users_query_response_401 import UsersQueryResponse401
from ...models.users_query_response_500 import UsersQueryResponse500
from ...types import Response


def _get_kwargs(
    *,
    body: UsersQueryBody,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/v1/api/users/query",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[
    Union[
        UsersQueryResponse200,
        UsersQueryResponse400,
        UsersQueryResponse401,
        UsersQueryResponse500,
    ]
]:
    if response.status_code == 200:
        response_200 = UsersQueryResponse200.from_dict(response.json())

        return response_200

    if response.status_code == 400:
        response_400 = UsersQueryResponse400.from_dict(response.json())

        return response_400

    if response.status_code == 401:
        response_401 = UsersQueryResponse401.from_dict(response.json())

        return response_401

    if response.status_code == 500:
        response_500 = UsersQueryResponse500.from_dict(response.json())

        return response_500

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[
    Union[
        UsersQueryResponse200,
        UsersQueryResponse400,
        UsersQueryResponse401,
        UsersQueryResponse500,
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
    body: UsersQueryBody,
) -> Response[
    Union[
        UsersQueryResponse200,
        UsersQueryResponse400,
        UsersQueryResponse401,
        UsersQueryResponse500,
    ]
]:
    """Query existing users

     Returns users that satisfy the given query.

    Args:
        body (UsersQueryBody):  Specifies which users to query.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[UsersQueryResponse200, UsersQueryResponse400, UsersQueryResponse401, UsersQueryResponse500]]
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
    body: UsersQueryBody,
) -> Optional[
    Union[
        UsersQueryResponse200,
        UsersQueryResponse400,
        UsersQueryResponse401,
        UsersQueryResponse500,
    ]
]:
    """Query existing users

     Returns users that satisfy the given query.

    Args:
        body (UsersQueryBody):  Specifies which users to query.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[UsersQueryResponse200, UsersQueryResponse400, UsersQueryResponse401, UsersQueryResponse500]
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: UsersQueryBody,
) -> Response[
    Union[
        UsersQueryResponse200,
        UsersQueryResponse400,
        UsersQueryResponse401,
        UsersQueryResponse500,
    ]
]:
    """Query existing users

     Returns users that satisfy the given query.

    Args:
        body (UsersQueryBody):  Specifies which users to query.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[UsersQueryResponse200, UsersQueryResponse400, UsersQueryResponse401, UsersQueryResponse500]]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    body: UsersQueryBody,
) -> Optional[
    Union[
        UsersQueryResponse200,
        UsersQueryResponse400,
        UsersQueryResponse401,
        UsersQueryResponse500,
    ]
]:
    """Query existing users

     Returns users that satisfy the given query.

    Args:
        body (UsersQueryBody):  Specifies which users to query.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[UsersQueryResponse200, UsersQueryResponse400, UsersQueryResponse401, UsersQueryResponse500]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
