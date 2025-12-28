from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.users_activate_body import UsersActivateBody
from ...models.users_activate_response_200 import UsersActivateResponse200
from ...models.users_activate_response_400 import UsersActivateResponse400
from ...models.users_activate_response_401 import UsersActivateResponse401
from ...models.users_activate_response_500 import UsersActivateResponse500
from ...types import Response


def _get_kwargs(
    *,
    body: UsersActivateBody,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/v1/api/users/activate",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[
    Union[
        UsersActivateResponse200,
        UsersActivateResponse400,
        UsersActivateResponse401,
        UsersActivateResponse500,
    ]
]:
    if response.status_code == 200:
        response_200 = UsersActivateResponse200.from_dict(response.json())

        return response_200

    if response.status_code == 400:
        response_400 = UsersActivateResponse400.from_dict(response.json())

        return response_400

    if response.status_code == 401:
        response_401 = UsersActivateResponse401.from_dict(response.json())

        return response_401

    if response.status_code == 500:
        response_500 = UsersActivateResponse500.from_dict(response.json())

        return response_500

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[
    Union[
        UsersActivateResponse200,
        UsersActivateResponse400,
        UsersActivateResponse401,
        UsersActivateResponse500,
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
    body: UsersActivateBody,
) -> Response[
    Union[
        UsersActivateResponse200,
        UsersActivateResponse400,
        UsersActivateResponse401,
        UsersActivateResponse500,
    ]
]:
    """Activate user

     Activate a previously deactivated user.

    Args:
        body (UsersActivateBody):  Request to update an existing user.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[UsersActivateResponse200, UsersActivateResponse400, UsersActivateResponse401, UsersActivateResponse500]]
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
    body: UsersActivateBody,
) -> Optional[
    Union[
        UsersActivateResponse200,
        UsersActivateResponse400,
        UsersActivateResponse401,
        UsersActivateResponse500,
    ]
]:
    """Activate user

     Activate a previously deactivated user.

    Args:
        body (UsersActivateBody):  Request to update an existing user.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[UsersActivateResponse200, UsersActivateResponse400, UsersActivateResponse401, UsersActivateResponse500]
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: UsersActivateBody,
) -> Response[
    Union[
        UsersActivateResponse200,
        UsersActivateResponse400,
        UsersActivateResponse401,
        UsersActivateResponse500,
    ]
]:
    """Activate user

     Activate a previously deactivated user.

    Args:
        body (UsersActivateBody):  Request to update an existing user.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[UsersActivateResponse200, UsersActivateResponse400, UsersActivateResponse401, UsersActivateResponse500]]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    body: UsersActivateBody,
) -> Optional[
    Union[
        UsersActivateResponse200,
        UsersActivateResponse400,
        UsersActivateResponse401,
        UsersActivateResponse500,
    ]
]:
    """Activate user

     Activate a previously deactivated user.

    Args:
        body (UsersActivateBody):  Request to update an existing user.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[UsersActivateResponse200, UsersActivateResponse400, UsersActivateResponse401, UsersActivateResponse500]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
