from http import HTTPStatus
from typing import Any, Optional, Union
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_orchestration_by_id_response import GetOrchestrationByIdResponse
from ...types import UNSET, Response


def _get_kwargs(
    *,
    id: UUID,
    token: str,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    json_id = str(id)
    params["id"] = json_id

    params["token"] = token

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/v1/api/orchestration/download",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[GetOrchestrationByIdResponse]:
    if response.status_code == 200:
        response_200 = GetOrchestrationByIdResponse.from_dict(response.json())

        return response_200

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[GetOrchestrationByIdResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    id: UUID,
    token: str,
) -> Response[GetOrchestrationByIdResponse]:
    """
    Args:
        id (UUID):
        token (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GetOrchestrationByIdResponse]
    """

    kwargs = _get_kwargs(
        id=id,
        token=token,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: Union[AuthenticatedClient, Client],
    id: UUID,
    token: str,
) -> Optional[GetOrchestrationByIdResponse]:
    """
    Args:
        id (UUID):
        token (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GetOrchestrationByIdResponse
    """

    return sync_detailed(
        client=client,
        id=id,
        token=token,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    id: UUID,
    token: str,
) -> Response[GetOrchestrationByIdResponse]:
    """
    Args:
        id (UUID):
        token (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GetOrchestrationByIdResponse]
    """

    kwargs = _get_kwargs(
        id=id,
        token=token,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    id: UUID,
    token: str,
) -> Optional[GetOrchestrationByIdResponse]:
    """
    Args:
        id (UUID):
        token (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GetOrchestrationByIdResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            id=id,
            token=token,
        )
    ).parsed
