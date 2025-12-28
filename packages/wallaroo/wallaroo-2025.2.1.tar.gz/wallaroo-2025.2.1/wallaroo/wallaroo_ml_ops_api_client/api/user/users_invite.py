from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.users_invite_body import UsersInviteBody
from ...models.users_invite_response_200 import UsersInviteResponse200
from ...models.users_invite_response_400 import UsersInviteResponse400
from ...models.users_invite_response_401 import UsersInviteResponse401
from ...models.users_invite_response_500 import UsersInviteResponse500
from ...types import Response


def _get_kwargs(
    *,
    body: UsersInviteBody,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/v1/api/users/invite",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[
    Union[
        UsersInviteResponse200,
        UsersInviteResponse400,
        UsersInviteResponse401,
        UsersInviteResponse500,
    ]
]:
    if response.status_code == 200:
        response_200 = UsersInviteResponse200.from_dict(response.json())

        return response_200

    if response.status_code == 400:
        response_400 = UsersInviteResponse400.from_dict(response.json())

        return response_400

    if response.status_code == 401:
        response_401 = UsersInviteResponse401.from_dict(response.json())

        return response_401

    if response.status_code == 500:
        response_500 = UsersInviteResponse500.from_dict(response.json())

        return response_500

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[
    Union[
        UsersInviteResponse200,
        UsersInviteResponse400,
        UsersInviteResponse401,
        UsersInviteResponse500,
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
    body: UsersInviteBody,
) -> Response[
    Union[
        UsersInviteResponse200,
        UsersInviteResponse400,
        UsersInviteResponse401,
        UsersInviteResponse500,
    ]
]:
    """Invite user to Wallaroo

     Invite a new user to your Wallaroo cluster by sending them an invitation email.

    Args:
        body (UsersInviteBody):  Invitation request for a new user.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[UsersInviteResponse200, UsersInviteResponse400, UsersInviteResponse401, UsersInviteResponse500]]
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
    body: UsersInviteBody,
) -> Optional[
    Union[
        UsersInviteResponse200,
        UsersInviteResponse400,
        UsersInviteResponse401,
        UsersInviteResponse500,
    ]
]:
    """Invite user to Wallaroo

     Invite a new user to your Wallaroo cluster by sending them an invitation email.

    Args:
        body (UsersInviteBody):  Invitation request for a new user.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[UsersInviteResponse200, UsersInviteResponse400, UsersInviteResponse401, UsersInviteResponse500]
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: UsersInviteBody,
) -> Response[
    Union[
        UsersInviteResponse200,
        UsersInviteResponse400,
        UsersInviteResponse401,
        UsersInviteResponse500,
    ]
]:
    """Invite user to Wallaroo

     Invite a new user to your Wallaroo cluster by sending them an invitation email.

    Args:
        body (UsersInviteBody):  Invitation request for a new user.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[UsersInviteResponse200, UsersInviteResponse400, UsersInviteResponse401, UsersInviteResponse500]]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    body: UsersInviteBody,
) -> Optional[
    Union[
        UsersInviteResponse200,
        UsersInviteResponse400,
        UsersInviteResponse401,
        UsersInviteResponse500,
    ]
]:
    """Invite user to Wallaroo

     Invite a new user to your Wallaroo cluster by sending them an invitation email.

    Args:
        body (UsersInviteBody):  Invitation request for a new user.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[UsersInviteResponse200, UsersInviteResponse400, UsersInviteResponse401, UsersInviteResponse500]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
