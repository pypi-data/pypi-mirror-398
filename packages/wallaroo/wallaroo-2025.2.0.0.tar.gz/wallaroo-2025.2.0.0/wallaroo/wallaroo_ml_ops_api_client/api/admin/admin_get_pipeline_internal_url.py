from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.admin_get_pipeline_internal_url_body import (
    AdminGetPipelineInternalUrlBody,
)
from ...models.admin_get_pipeline_internal_url_response_200 import (
    AdminGetPipelineInternalUrlResponse200,
)
from ...models.admin_get_pipeline_internal_url_response_400 import (
    AdminGetPipelineInternalUrlResponse400,
)
from ...models.admin_get_pipeline_internal_url_response_401 import (
    AdminGetPipelineInternalUrlResponse401,
)
from ...models.admin_get_pipeline_internal_url_response_500 import (
    AdminGetPipelineInternalUrlResponse500,
)
from ...types import Response


def _get_kwargs(
    *,
    body: AdminGetPipelineInternalUrlBody,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/v1/api/admin/get_pipeline_internal_url",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[
    Union[
        AdminGetPipelineInternalUrlResponse200,
        AdminGetPipelineInternalUrlResponse400,
        AdminGetPipelineInternalUrlResponse401,
        AdminGetPipelineInternalUrlResponse500,
    ]
]:
    if response.status_code == 200:
        response_200 = AdminGetPipelineInternalUrlResponse200.from_dict(response.json())

        return response_200

    if response.status_code == 400:
        response_400 = AdminGetPipelineInternalUrlResponse400.from_dict(response.json())

        return response_400

    if response.status_code == 401:
        response_401 = AdminGetPipelineInternalUrlResponse401.from_dict(response.json())

        return response_401

    if response.status_code == 500:
        response_500 = AdminGetPipelineInternalUrlResponse500.from_dict(response.json())

        return response_500

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[
    Union[
        AdminGetPipelineInternalUrlResponse200,
        AdminGetPipelineInternalUrlResponse400,
        AdminGetPipelineInternalUrlResponse401,
        AdminGetPipelineInternalUrlResponse500,
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
    body: AdminGetPipelineInternalUrlBody,
) -> Response[
    Union[
        AdminGetPipelineInternalUrlResponse200,
        AdminGetPipelineInternalUrlResponse400,
        AdminGetPipelineInternalUrlResponse401,
        AdminGetPipelineInternalUrlResponse500,
    ]
]:
    """Returns the URL for the given pipeline that clients may send inferences to from inside of the
    cluster.

     Returns the internal inference URL for a given pipeline.

    Args:
        body (AdminGetPipelineInternalUrlBody):  Request for pipeline URL-related operations.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[AdminGetPipelineInternalUrlResponse200, AdminGetPipelineInternalUrlResponse400, AdminGetPipelineInternalUrlResponse401, AdminGetPipelineInternalUrlResponse500]]
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
    body: AdminGetPipelineInternalUrlBody,
) -> Optional[
    Union[
        AdminGetPipelineInternalUrlResponse200,
        AdminGetPipelineInternalUrlResponse400,
        AdminGetPipelineInternalUrlResponse401,
        AdminGetPipelineInternalUrlResponse500,
    ]
]:
    """Returns the URL for the given pipeline that clients may send inferences to from inside of the
    cluster.

     Returns the internal inference URL for a given pipeline.

    Args:
        body (AdminGetPipelineInternalUrlBody):  Request for pipeline URL-related operations.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[AdminGetPipelineInternalUrlResponse200, AdminGetPipelineInternalUrlResponse400, AdminGetPipelineInternalUrlResponse401, AdminGetPipelineInternalUrlResponse500]
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: AdminGetPipelineInternalUrlBody,
) -> Response[
    Union[
        AdminGetPipelineInternalUrlResponse200,
        AdminGetPipelineInternalUrlResponse400,
        AdminGetPipelineInternalUrlResponse401,
        AdminGetPipelineInternalUrlResponse500,
    ]
]:
    """Returns the URL for the given pipeline that clients may send inferences to from inside of the
    cluster.

     Returns the internal inference URL for a given pipeline.

    Args:
        body (AdminGetPipelineInternalUrlBody):  Request for pipeline URL-related operations.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[AdminGetPipelineInternalUrlResponse200, AdminGetPipelineInternalUrlResponse400, AdminGetPipelineInternalUrlResponse401, AdminGetPipelineInternalUrlResponse500]]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    body: AdminGetPipelineInternalUrlBody,
) -> Optional[
    Union[
        AdminGetPipelineInternalUrlResponse200,
        AdminGetPipelineInternalUrlResponse400,
        AdminGetPipelineInternalUrlResponse401,
        AdminGetPipelineInternalUrlResponse500,
    ]
]:
    """Returns the URL for the given pipeline that clients may send inferences to from inside of the
    cluster.

     Returns the internal inference URL for a given pipeline.

    Args:
        body (AdminGetPipelineInternalUrlBody):  Request for pipeline URL-related operations.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[AdminGetPipelineInternalUrlResponse200, AdminGetPipelineInternalUrlResponse400, AdminGetPipelineInternalUrlResponse401, AdminGetPipelineInternalUrlResponse500]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
