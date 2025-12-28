from http import HTTPStatus
from typing import Any, Optional, Union, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.users_edit_body import UsersEditBody
from ...models.users_edit_response_200_type_0 import UsersEditResponse200Type0
from ...models.users_edit_response_400 import UsersEditResponse400
from ...models.users_edit_response_401 import UsersEditResponse401
from ...models.users_edit_response_500 import UsersEditResponse500
from ...types import Response


def _get_kwargs(
    *,
    body: UsersEditBody,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/v1/api/user",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[
    Union[
        Union["UsersEditResponse200Type0", None],
        UsersEditResponse400,
        UsersEditResponse401,
        UsersEditResponse500,
    ]
]:
    if response.status_code == 200:

        def _parse_response_200(
            data: object,
        ) -> Union["UsersEditResponse200Type0", None]:
            if data is None:
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                response_200_type_0 = UsersEditResponse200Type0.from_dict(data)

                return response_200_type_0
            except:  # noqa: E722
                pass
            return cast(Union["UsersEditResponse200Type0", None], data)

        response_200 = _parse_response_200(response.json())

        return response_200

    if response.status_code == 400:
        response_400 = UsersEditResponse400.from_dict(response.json())

        return response_400

    if response.status_code == 401:
        response_401 = UsersEditResponse401.from_dict(response.json())

        return response_401

    if response.status_code == 500:
        response_500 = UsersEditResponse500.from_dict(response.json())

        return response_500

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[
    Union[
        Union["UsersEditResponse200Type0", None],
        UsersEditResponse400,
        UsersEditResponse401,
        UsersEditResponse500,
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
    body: UsersEditBody,
) -> Response[
    Union[
        Union["UsersEditResponse200Type0", None],
        UsersEditResponse400,
        UsersEditResponse401,
        UsersEditResponse500,
    ]
]:
    """Edit users in Wallaroo

    Args:
        body (UsersEditBody):  Edit user properties in Keycloak.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Union['UsersEditResponse200Type0', None], UsersEditResponse400, UsersEditResponse401, UsersEditResponse500]]
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
    body: UsersEditBody,
) -> Optional[
    Union[
        Union["UsersEditResponse200Type0", None],
        UsersEditResponse400,
        UsersEditResponse401,
        UsersEditResponse500,
    ]
]:
    """Edit users in Wallaroo

    Args:
        body (UsersEditBody):  Edit user properties in Keycloak.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Union['UsersEditResponse200Type0', None], UsersEditResponse400, UsersEditResponse401, UsersEditResponse500]
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: UsersEditBody,
) -> Response[
    Union[
        Union["UsersEditResponse200Type0", None],
        UsersEditResponse400,
        UsersEditResponse401,
        UsersEditResponse500,
    ]
]:
    """Edit users in Wallaroo

    Args:
        body (UsersEditBody):  Edit user properties in Keycloak.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Union['UsersEditResponse200Type0', None], UsersEditResponse400, UsersEditResponse401, UsersEditResponse500]]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    body: UsersEditBody,
) -> Optional[
    Union[
        Union["UsersEditResponse200Type0", None],
        UsersEditResponse400,
        UsersEditResponse401,
        UsersEditResponse500,
    ]
]:
    """Edit users in Wallaroo

    Args:
        body (UsersEditBody):  Edit user properties in Keycloak.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Union['UsersEditResponse200Type0', None], UsersEditResponse400, UsersEditResponse401, UsersEditResponse500]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
