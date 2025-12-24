from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.assays_list_body import AssaysListBody
from ...models.assays_list_response_200_item import AssaysListResponse200Item
from ...models.assays_list_response_400 import AssaysListResponse400
from ...models.assays_list_response_401 import AssaysListResponse401
from ...models.assays_list_response_500 import AssaysListResponse500
from ...types import Response


def _get_kwargs(
    *,
    body: AssaysListBody,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/v1/api/assays/list",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[
    Union[
        AssaysListResponse400,
        AssaysListResponse401,
        AssaysListResponse500,
        list["AssaysListResponse200Item"],
    ]
]:
    if response.status_code == 200:
        response_200 = []
        _response_200 = response.json()
        for response_200_item_data in _response_200:
            response_200_item = AssaysListResponse200Item.from_dict(
                response_200_item_data
            )

            response_200.append(response_200_item)

        return response_200

    if response.status_code == 400:
        response_400 = AssaysListResponse400.from_dict(response.json())

        return response_400

    if response.status_code == 401:
        response_401 = AssaysListResponse401.from_dict(response.json())

        return response_401

    if response.status_code == 500:
        response_500 = AssaysListResponse500.from_dict(response.json())

        return response_500

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[
    Union[
        AssaysListResponse400,
        AssaysListResponse401,
        AssaysListResponse500,
        list["AssaysListResponse200Item"],
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
    body: AssaysListBody,
) -> Response[
    Union[
        AssaysListResponse400,
        AssaysListResponse401,
        AssaysListResponse500,
        list["AssaysListResponse200Item"],
    ]
]:
    """List assays

     Returns the list of existing assays.

    Args:
        body (AssaysListBody):  Request for list of assays.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[AssaysListResponse400, AssaysListResponse401, AssaysListResponse500, list['AssaysListResponse200Item']]]
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
    body: AssaysListBody,
) -> Optional[
    Union[
        AssaysListResponse400,
        AssaysListResponse401,
        AssaysListResponse500,
        list["AssaysListResponse200Item"],
    ]
]:
    """List assays

     Returns the list of existing assays.

    Args:
        body (AssaysListBody):  Request for list of assays.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[AssaysListResponse400, AssaysListResponse401, AssaysListResponse500, list['AssaysListResponse200Item']]
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: AssaysListBody,
) -> Response[
    Union[
        AssaysListResponse400,
        AssaysListResponse401,
        AssaysListResponse500,
        list["AssaysListResponse200Item"],
    ]
]:
    """List assays

     Returns the list of existing assays.

    Args:
        body (AssaysListBody):  Request for list of assays.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[AssaysListResponse400, AssaysListResponse401, AssaysListResponse500, list['AssaysListResponse200Item']]]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    body: AssaysListBody,
) -> Optional[
    Union[
        AssaysListResponse400,
        AssaysListResponse401,
        AssaysListResponse500,
        list["AssaysListResponse200Item"],
    ]
]:
    """List assays

     Returns the list of existing assays.

    Args:
        body (AssaysListBody):  Request for list of assays.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[AssaysListResponse400, AssaysListResponse401, AssaysListResponse500, list['AssaysListResponse200Item']]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
