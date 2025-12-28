from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.dbfs_list_response_file_with_full_path import (
    DbfsListResponseFileWithFullPath,
)
from ...models.list_registry_model_version_artifacts_request import (
    ListRegistryModelVersionArtifactsRequest,
)
from ...types import Response


def _get_kwargs(
    *,
    body: ListRegistryModelVersionArtifactsRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/v1/api/models/list_registry_model_version_artifacts",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[list["DbfsListResponseFileWithFullPath"]]:
    if response.status_code == 200:
        response_200 = []
        _response_200 = response.json()
        for response_200_item_data in _response_200:
            response_200_item = DbfsListResponseFileWithFullPath.from_dict(
                response_200_item_data
            )

            response_200.append(response_200_item)

        return response_200

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[list["DbfsListResponseFileWithFullPath"]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: ListRegistryModelVersionArtifactsRequest,
) -> Response[list["DbfsListResponseFileWithFullPath"]]:
    """
    Args:
        body (ListRegistryModelVersionArtifactsRequest): Payload for the List Registry Model
            Version Artifacts call.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[list['DbfsListResponseFileWithFullPath']]
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
    body: ListRegistryModelVersionArtifactsRequest,
) -> Optional[list["DbfsListResponseFileWithFullPath"]]:
    """
    Args:
        body (ListRegistryModelVersionArtifactsRequest): Payload for the List Registry Model
            Version Artifacts call.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        list['DbfsListResponseFileWithFullPath']
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: ListRegistryModelVersionArtifactsRequest,
) -> Response[list["DbfsListResponseFileWithFullPath"]]:
    """
    Args:
        body (ListRegistryModelVersionArtifactsRequest): Payload for the List Registry Model
            Version Artifacts call.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[list['DbfsListResponseFileWithFullPath']]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    body: ListRegistryModelVersionArtifactsRequest,
) -> Optional[list["DbfsListResponseFileWithFullPath"]]:
    """
    Args:
        body (ListRegistryModelVersionArtifactsRequest): Payload for the List Registry Model
            Version Artifacts call.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        list['DbfsListResponseFileWithFullPath']
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
