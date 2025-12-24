from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.plateau_get_pipeline_topic_name_body import (
    PlateauGetPipelineTopicNameBody,
)
from ...models.plateau_get_pipeline_topic_name_response_200 import (
    PlateauGetPipelineTopicNameResponse200,
)
from ...models.plateau_get_pipeline_topic_name_response_400 import (
    PlateauGetPipelineTopicNameResponse400,
)
from ...models.plateau_get_pipeline_topic_name_response_401 import (
    PlateauGetPipelineTopicNameResponse401,
)
from ...models.plateau_get_pipeline_topic_name_response_500 import (
    PlateauGetPipelineTopicNameResponse500,
)
from ...types import Response


def _get_kwargs(
    *,
    body: PlateauGetPipelineTopicNameBody,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/v1/api/plateau/get_pipeline_topic_name",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[
    Union[
        PlateauGetPipelineTopicNameResponse200,
        PlateauGetPipelineTopicNameResponse400,
        PlateauGetPipelineTopicNameResponse401,
        PlateauGetPipelineTopicNameResponse500,
    ]
]:
    if response.status_code == 200:
        response_200 = PlateauGetPipelineTopicNameResponse200.from_dict(response.json())

        return response_200

    if response.status_code == 400:
        response_400 = PlateauGetPipelineTopicNameResponse400.from_dict(response.json())

        return response_400

    if response.status_code == 401:
        response_401 = PlateauGetPipelineTopicNameResponse401.from_dict(response.json())

        return response_401

    if response.status_code == 500:
        response_500 = PlateauGetPipelineTopicNameResponse500.from_dict(response.json())

        return response_500

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[
    Union[
        PlateauGetPipelineTopicNameResponse200,
        PlateauGetPipelineTopicNameResponse400,
        PlateauGetPipelineTopicNameResponse401,
        PlateauGetPipelineTopicNameResponse500,
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
    body: PlateauGetPipelineTopicNameBody,
) -> Response[
    Union[
        PlateauGetPipelineTopicNameResponse200,
        PlateauGetPipelineTopicNameResponse400,
        PlateauGetPipelineTopicNameResponse401,
        PlateauGetPipelineTopicNameResponse500,
    ]
]:
    """Get pipeline topic name

     Returns the given pipeline's topic name.

    Args:
        body (PlateauGetPipelineTopicNameBody):  Request for pipeline topic name.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[PlateauGetPipelineTopicNameResponse200, PlateauGetPipelineTopicNameResponse400, PlateauGetPipelineTopicNameResponse401, PlateauGetPipelineTopicNameResponse500]]
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
    body: PlateauGetPipelineTopicNameBody,
) -> Optional[
    Union[
        PlateauGetPipelineTopicNameResponse200,
        PlateauGetPipelineTopicNameResponse400,
        PlateauGetPipelineTopicNameResponse401,
        PlateauGetPipelineTopicNameResponse500,
    ]
]:
    """Get pipeline topic name

     Returns the given pipeline's topic name.

    Args:
        body (PlateauGetPipelineTopicNameBody):  Request for pipeline topic name.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[PlateauGetPipelineTopicNameResponse200, PlateauGetPipelineTopicNameResponse400, PlateauGetPipelineTopicNameResponse401, PlateauGetPipelineTopicNameResponse500]
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: PlateauGetPipelineTopicNameBody,
) -> Response[
    Union[
        PlateauGetPipelineTopicNameResponse200,
        PlateauGetPipelineTopicNameResponse400,
        PlateauGetPipelineTopicNameResponse401,
        PlateauGetPipelineTopicNameResponse500,
    ]
]:
    """Get pipeline topic name

     Returns the given pipeline's topic name.

    Args:
        body (PlateauGetPipelineTopicNameBody):  Request for pipeline topic name.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[PlateauGetPipelineTopicNameResponse200, PlateauGetPipelineTopicNameResponse400, PlateauGetPipelineTopicNameResponse401, PlateauGetPipelineTopicNameResponse500]]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    body: PlateauGetPipelineTopicNameBody,
) -> Optional[
    Union[
        PlateauGetPipelineTopicNameResponse200,
        PlateauGetPipelineTopicNameResponse400,
        PlateauGetPipelineTopicNameResponse401,
        PlateauGetPipelineTopicNameResponse500,
    ]
]:
    """Get pipeline topic name

     Returns the given pipeline's topic name.

    Args:
        body (PlateauGetPipelineTopicNameBody):  Request for pipeline topic name.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[PlateauGetPipelineTopicNameResponse200, PlateauGetPipelineTopicNameResponse400, PlateauGetPipelineTopicNameResponse401, PlateauGetPipelineTopicNameResponse500]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
