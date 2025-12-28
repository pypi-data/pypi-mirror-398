from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.models_list_versions_body import ModelsListVersionsBody
from ...models.models_list_versions_response_200_item import (
    ModelsListVersionsResponse200Item,
)
from ...models.models_list_versions_response_400 import ModelsListVersionsResponse400
from ...models.models_list_versions_response_401 import ModelsListVersionsResponse401
from ...models.models_list_versions_response_500 import ModelsListVersionsResponse500
from ...types import Response


def _get_kwargs(
    *,
    body: ModelsListVersionsBody,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/v1/api/models/list_versions",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[
    Union[
        ModelsListVersionsResponse400,
        ModelsListVersionsResponse401,
        ModelsListVersionsResponse500,
        list["ModelsListVersionsResponse200Item"],
    ]
]:
    if response.status_code == 200:
        response_200 = []
        _response_200 = response.json()
        for response_200_item_data in _response_200:
            response_200_item = ModelsListVersionsResponse200Item.from_dict(
                response_200_item_data
            )

            response_200.append(response_200_item)

        return response_200

    if response.status_code == 400:
        response_400 = ModelsListVersionsResponse400.from_dict(response.json())

        return response_400

    if response.status_code == 401:
        response_401 = ModelsListVersionsResponse401.from_dict(response.json())

        return response_401

    if response.status_code == 500:
        response_500 = ModelsListVersionsResponse500.from_dict(response.json())

        return response_500

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[
    Union[
        ModelsListVersionsResponse400,
        ModelsListVersionsResponse401,
        ModelsListVersionsResponse500,
        list["ModelsListVersionsResponse200Item"],
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
    body: ModelsListVersionsBody,
) -> Response[
    Union[
        ModelsListVersionsResponse400,
        ModelsListVersionsResponse401,
        ModelsListVersionsResponse500,
        list["ModelsListVersionsResponse200Item"],
    ]
]:
    """Retrieve versions of a model

     Returns all versions for a given model.

    Args:
        body (ModelsListVersionsBody):  Request for getting model versions

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[ModelsListVersionsResponse400, ModelsListVersionsResponse401, ModelsListVersionsResponse500, list['ModelsListVersionsResponse200Item']]]
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
    body: ModelsListVersionsBody,
) -> Optional[
    Union[
        ModelsListVersionsResponse400,
        ModelsListVersionsResponse401,
        ModelsListVersionsResponse500,
        list["ModelsListVersionsResponse200Item"],
    ]
]:
    """Retrieve versions of a model

     Returns all versions for a given model.

    Args:
        body (ModelsListVersionsBody):  Request for getting model versions

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[ModelsListVersionsResponse400, ModelsListVersionsResponse401, ModelsListVersionsResponse500, list['ModelsListVersionsResponse200Item']]
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: ModelsListVersionsBody,
) -> Response[
    Union[
        ModelsListVersionsResponse400,
        ModelsListVersionsResponse401,
        ModelsListVersionsResponse500,
        list["ModelsListVersionsResponse200Item"],
    ]
]:
    """Retrieve versions of a model

     Returns all versions for a given model.

    Args:
        body (ModelsListVersionsBody):  Request for getting model versions

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[ModelsListVersionsResponse400, ModelsListVersionsResponse401, ModelsListVersionsResponse500, list['ModelsListVersionsResponse200Item']]]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    body: ModelsListVersionsBody,
) -> Optional[
    Union[
        ModelsListVersionsResponse400,
        ModelsListVersionsResponse401,
        ModelsListVersionsResponse500,
        list["ModelsListVersionsResponse200Item"],
    ]
]:
    """Retrieve versions of a model

     Returns all versions for a given model.

    Args:
        body (ModelsListVersionsBody):  Request for getting model versions

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[ModelsListVersionsResponse400, ModelsListVersionsResponse401, ModelsListVersionsResponse500, list['ModelsListVersionsResponse200Item']]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
