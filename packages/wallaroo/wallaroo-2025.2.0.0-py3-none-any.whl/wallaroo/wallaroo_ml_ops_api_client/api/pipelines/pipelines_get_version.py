from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.pipelines_get_version_body import PipelinesGetVersionBody
from ...models.pipelines_get_version_response_200 import PipelinesGetVersionResponse200
from ...models.pipelines_get_version_response_400 import PipelinesGetVersionResponse400
from ...models.pipelines_get_version_response_401 import PipelinesGetVersionResponse401
from ...models.pipelines_get_version_response_500 import PipelinesGetVersionResponse500
from ...types import Response


def _get_kwargs(
    *,
    body: PipelinesGetVersionBody,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/v1/api/pipelines/get_version",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[
    Union[
        PipelinesGetVersionResponse200,
        PipelinesGetVersionResponse400,
        PipelinesGetVersionResponse401,
        PipelinesGetVersionResponse500,
    ]
]:
    if response.status_code == 200:
        response_200 = PipelinesGetVersionResponse200.from_dict(response.json())

        return response_200

    if response.status_code == 400:
        response_400 = PipelinesGetVersionResponse400.from_dict(response.json())

        return response_400

    if response.status_code == 401:
        response_401 = PipelinesGetVersionResponse401.from_dict(response.json())

        return response_401

    if response.status_code == 500:
        response_500 = PipelinesGetVersionResponse500.from_dict(response.json())

        return response_500

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[
    Union[
        PipelinesGetVersionResponse200,
        PipelinesGetVersionResponse400,
        PipelinesGetVersionResponse401,
        PipelinesGetVersionResponse500,
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
    body: PipelinesGetVersionBody,
) -> Response[
    Union[
        PipelinesGetVersionResponse200,
        PipelinesGetVersionResponse400,
        PipelinesGetVersionResponse401,
        PipelinesGetVersionResponse500,
    ]
]:
    """Get pipeline version

     Undeploys a previously deployed pipeline.

    Args:
        body (PipelinesGetVersionBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[PipelinesGetVersionResponse200, PipelinesGetVersionResponse400, PipelinesGetVersionResponse401, PipelinesGetVersionResponse500]]
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
    body: PipelinesGetVersionBody,
) -> Optional[
    Union[
        PipelinesGetVersionResponse200,
        PipelinesGetVersionResponse400,
        PipelinesGetVersionResponse401,
        PipelinesGetVersionResponse500,
    ]
]:
    """Get pipeline version

     Undeploys a previously deployed pipeline.

    Args:
        body (PipelinesGetVersionBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[PipelinesGetVersionResponse200, PipelinesGetVersionResponse400, PipelinesGetVersionResponse401, PipelinesGetVersionResponse500]
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: PipelinesGetVersionBody,
) -> Response[
    Union[
        PipelinesGetVersionResponse200,
        PipelinesGetVersionResponse400,
        PipelinesGetVersionResponse401,
        PipelinesGetVersionResponse500,
    ]
]:
    """Get pipeline version

     Undeploys a previously deployed pipeline.

    Args:
        body (PipelinesGetVersionBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[PipelinesGetVersionResponse200, PipelinesGetVersionResponse400, PipelinesGetVersionResponse401, PipelinesGetVersionResponse500]]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    body: PipelinesGetVersionBody,
) -> Optional[
    Union[
        PipelinesGetVersionResponse200,
        PipelinesGetVersionResponse400,
        PipelinesGetVersionResponse401,
        PipelinesGetVersionResponse500,
    ]
]:
    """Get pipeline version

     Undeploys a previously deployed pipeline.

    Args:
        body (PipelinesGetVersionBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[PipelinesGetVersionResponse200, PipelinesGetVersionResponse400, PipelinesGetVersionResponse401, PipelinesGetVersionResponse500]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
