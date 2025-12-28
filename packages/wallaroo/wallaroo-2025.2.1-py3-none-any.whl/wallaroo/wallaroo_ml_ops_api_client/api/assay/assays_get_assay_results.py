from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.assays_get_assay_results_body import AssaysGetAssayResultsBody
from ...models.assays_get_assay_results_response_200_item import (
    AssaysGetAssayResultsResponse200Item,
)
from ...models.assays_get_assay_results_response_500 import (
    AssaysGetAssayResultsResponse500,
)
from ...types import Response


def _get_kwargs(
    *,
    body: AssaysGetAssayResultsBody,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/v1/api/assays/get_assay_results",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[
    Union[
        AssaysGetAssayResultsResponse500, list["AssaysGetAssayResultsResponse200Item"]
    ]
]:
    if response.status_code == 200:
        response_200 = []
        _response_200 = response.json()
        for response_200_item_data in _response_200:
            response_200_item = AssaysGetAssayResultsResponse200Item.from_dict(
                response_200_item_data
            )

            response_200.append(response_200_item)

        return response_200

    if response.status_code == 500:
        response_500 = AssaysGetAssayResultsResponse500.from_dict(response.json())

        return response_500

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[
    Union[
        AssaysGetAssayResultsResponse500, list["AssaysGetAssayResultsResponse200Item"]
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
    body: AssaysGetAssayResultsBody,
) -> Response[
    Union[
        AssaysGetAssayResultsResponse500, list["AssaysGetAssayResultsResponse200Item"]
    ]
]:
    """Temporary mockup to get get assay results by assay_id.

     Returns assay results.

    Args:
        body (AssaysGetAssayResultsBody):  Request to return assay results.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[AssaysGetAssayResultsResponse500, list['AssaysGetAssayResultsResponse200Item']]]
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
    body: AssaysGetAssayResultsBody,
) -> Optional[
    Union[
        AssaysGetAssayResultsResponse500, list["AssaysGetAssayResultsResponse200Item"]
    ]
]:
    """Temporary mockup to get get assay results by assay_id.

     Returns assay results.

    Args:
        body (AssaysGetAssayResultsBody):  Request to return assay results.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[AssaysGetAssayResultsResponse500, list['AssaysGetAssayResultsResponse200Item']]
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: AssaysGetAssayResultsBody,
) -> Response[
    Union[
        AssaysGetAssayResultsResponse500, list["AssaysGetAssayResultsResponse200Item"]
    ]
]:
    """Temporary mockup to get get assay results by assay_id.

     Returns assay results.

    Args:
        body (AssaysGetAssayResultsBody):  Request to return assay results.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[AssaysGetAssayResultsResponse500, list['AssaysGetAssayResultsResponse200Item']]]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    body: AssaysGetAssayResultsBody,
) -> Optional[
    Union[
        AssaysGetAssayResultsResponse500, list["AssaysGetAssayResultsResponse200Item"]
    ]
]:
    """Temporary mockup to get get assay results by assay_id.

     Returns assay results.

    Args:
        body (AssaysGetAssayResultsBody):  Request to return assay results.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[AssaysGetAssayResultsResponse500, list['AssaysGetAssayResultsResponse200Item']]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
