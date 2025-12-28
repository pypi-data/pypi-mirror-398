from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.assays_filter_body import AssaysFilterBody
from ...models.assays_filter_response_200_item import AssaysFilterResponse200Item
from ...models.assays_filter_response_500 import AssaysFilterResponse500
from ...types import Response


def _get_kwargs(
    *,
    body: AssaysFilterBody,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/v1/api/assays/filter",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[AssaysFilterResponse500, list["AssaysFilterResponse200Item"]]]:
    if response.status_code == 200:
        response_200 = []
        _response_200 = response.json()
        for response_200_item_data in _response_200:
            response_200_item = AssaysFilterResponse200Item.from_dict(
                response_200_item_data
            )

            response_200.append(response_200_item)

        return response_200

    if response.status_code == 500:
        response_500 = AssaysFilterResponse500.from_dict(response.json())

        return response_500

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[Union[AssaysFilterResponse500, list["AssaysFilterResponse200Item"]]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: AssaysFilterBody,
) -> Response[Union[AssaysFilterResponse500, list["AssaysFilterResponse200Item"]]]:
    """Retrieve assay configs, filtered and sorted as requested.

     Returns the list of existing assays filterable by assay name, id, active, creation date, and last
    run date.

    Args:
        body (AssaysFilterBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[AssaysFilterResponse500, list['AssaysFilterResponse200Item']]]
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
    body: AssaysFilterBody,
) -> Optional[Union[AssaysFilterResponse500, list["AssaysFilterResponse200Item"]]]:
    """Retrieve assay configs, filtered and sorted as requested.

     Returns the list of existing assays filterable by assay name, id, active, creation date, and last
    run date.

    Args:
        body (AssaysFilterBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[AssaysFilterResponse500, list['AssaysFilterResponse200Item']]
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: AssaysFilterBody,
) -> Response[Union[AssaysFilterResponse500, list["AssaysFilterResponse200Item"]]]:
    """Retrieve assay configs, filtered and sorted as requested.

     Returns the list of existing assays filterable by assay name, id, active, creation date, and last
    run date.

    Args:
        body (AssaysFilterBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[AssaysFilterResponse500, list['AssaysFilterResponse200Item']]]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    body: AssaysFilterBody,
) -> Optional[Union[AssaysFilterResponse500, list["AssaysFilterResponse200Item"]]]:
    """Retrieve assay configs, filtered and sorted as requested.

     Returns the list of existing assays filterable by assay name, id, active, creation date, and last
    run date.

    Args:
        body (AssaysFilterBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[AssaysFilterResponse500, list['AssaysFilterResponse200Item']]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
