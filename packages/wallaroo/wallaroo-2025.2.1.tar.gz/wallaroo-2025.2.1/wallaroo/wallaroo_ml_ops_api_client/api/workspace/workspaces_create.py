from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.workspaces_create_body import WorkspacesCreateBody
from ...models.workspaces_create_response_200 import WorkspacesCreateResponse200
from ...models.workspaces_create_response_400 import WorkspacesCreateResponse400
from ...models.workspaces_create_response_401 import WorkspacesCreateResponse401
from ...models.workspaces_create_response_500 import WorkspacesCreateResponse500
from ...types import Response


def _get_kwargs(
    *,
    body: WorkspacesCreateBody,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/v1/api/workspaces/create",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[
    Union[
        WorkspacesCreateResponse200,
        WorkspacesCreateResponse400,
        WorkspacesCreateResponse401,
        WorkspacesCreateResponse500,
    ]
]:
    if response.status_code == 200:
        response_200 = WorkspacesCreateResponse200.from_dict(response.json())

        return response_200

    if response.status_code == 400:
        response_400 = WorkspacesCreateResponse400.from_dict(response.json())

        return response_400

    if response.status_code == 401:
        response_401 = WorkspacesCreateResponse401.from_dict(response.json())

        return response_401

    if response.status_code == 500:
        response_500 = WorkspacesCreateResponse500.from_dict(response.json())

        return response_500

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[
    Union[
        WorkspacesCreateResponse200,
        WorkspacesCreateResponse400,
        WorkspacesCreateResponse401,
        WorkspacesCreateResponse500,
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
    body: WorkspacesCreateBody,
) -> Response[
    Union[
        WorkspacesCreateResponse200,
        WorkspacesCreateResponse400,
        WorkspacesCreateResponse401,
        WorkspacesCreateResponse500,
    ]
]:
    """Create a workspace

     Create a new Workspace

    Args:
        body (WorkspacesCreateBody):  Request to create a new Workspace

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[WorkspacesCreateResponse200, WorkspacesCreateResponse400, WorkspacesCreateResponse401, WorkspacesCreateResponse500]]
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
    body: WorkspacesCreateBody,
) -> Optional[
    Union[
        WorkspacesCreateResponse200,
        WorkspacesCreateResponse400,
        WorkspacesCreateResponse401,
        WorkspacesCreateResponse500,
    ]
]:
    """Create a workspace

     Create a new Workspace

    Args:
        body (WorkspacesCreateBody):  Request to create a new Workspace

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[WorkspacesCreateResponse200, WorkspacesCreateResponse400, WorkspacesCreateResponse401, WorkspacesCreateResponse500]
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: WorkspacesCreateBody,
) -> Response[
    Union[
        WorkspacesCreateResponse200,
        WorkspacesCreateResponse400,
        WorkspacesCreateResponse401,
        WorkspacesCreateResponse500,
    ]
]:
    """Create a workspace

     Create a new Workspace

    Args:
        body (WorkspacesCreateBody):  Request to create a new Workspace

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[WorkspacesCreateResponse200, WorkspacesCreateResponse400, WorkspacesCreateResponse401, WorkspacesCreateResponse500]]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    body: WorkspacesCreateBody,
) -> Optional[
    Union[
        WorkspacesCreateResponse200,
        WorkspacesCreateResponse400,
        WorkspacesCreateResponse401,
        WorkspacesCreateResponse500,
    ]
]:
    """Create a workspace

     Create a new Workspace

    Args:
        body (WorkspacesCreateBody):  Request to create a new Workspace

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[WorkspacesCreateResponse200, WorkspacesCreateResponse400, WorkspacesCreateResponse401, WorkspacesCreateResponse500]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
