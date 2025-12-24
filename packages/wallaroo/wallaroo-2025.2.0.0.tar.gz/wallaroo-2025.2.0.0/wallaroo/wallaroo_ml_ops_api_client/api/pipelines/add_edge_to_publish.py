from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.add_edge_to_publish_body import AddEdgeToPublishBody
from ...models.add_edge_to_publish_response_201 import AddEdgeToPublishResponse201
from ...types import Response


def _get_kwargs(
    *,
    body: AddEdgeToPublishBody,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/v1/api/pipelines/add_edge_to_publish",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[AddEdgeToPublishResponse201]:
    if response.status_code == 201:
        response_201 = AddEdgeToPublishResponse201.from_dict(response.json())

        return response_201

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[AddEdgeToPublishResponse201]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: AddEdgeToPublishBody,
) -> Response[AddEdgeToPublishResponse201]:
    """Publishes a given pipeline for deployment on the edge.

    Args:
        body (AddEdgeToPublishBody): Request to publish a pipeline.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[AddEdgeToPublishResponse201]
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
    body: AddEdgeToPublishBody,
) -> Optional[AddEdgeToPublishResponse201]:
    """Publishes a given pipeline for deployment on the edge.

    Args:
        body (AddEdgeToPublishBody): Request to publish a pipeline.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        AddEdgeToPublishResponse201
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: AddEdgeToPublishBody,
) -> Response[AddEdgeToPublishResponse201]:
    """Publishes a given pipeline for deployment on the edge.

    Args:
        body (AddEdgeToPublishBody): Request to publish a pipeline.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[AddEdgeToPublishResponse201]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    body: AddEdgeToPublishBody,
) -> Optional[AddEdgeToPublishResponse201]:
    """Publishes a given pipeline for deployment on the edge.

    Args:
        body (AddEdgeToPublishBody): Request to publish a pipeline.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        AddEdgeToPublishResponse201
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
