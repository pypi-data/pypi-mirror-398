from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.assays_run_interactive_body import AssaysRunInteractiveBody
from ...models.assays_run_interactive_response_200_item import (
    AssaysRunInteractiveResponse200Item,
)
from ...models.assays_run_interactive_response_400 import (
    AssaysRunInteractiveResponse400,
)
from ...models.assays_run_interactive_response_401 import (
    AssaysRunInteractiveResponse401,
)
from ...models.assays_run_interactive_response_500 import (
    AssaysRunInteractiveResponse500,
)
from ...types import Response


def _get_kwargs(
    *,
    body: AssaysRunInteractiveBody,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/v1/api/assays/run_interactive",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[
    Union[
        AssaysRunInteractiveResponse400,
        AssaysRunInteractiveResponse401,
        AssaysRunInteractiveResponse500,
        list["AssaysRunInteractiveResponse200Item"],
    ]
]:
    if response.status_code == 200:
        response_200 = []
        _response_200 = response.json()
        for response_200_item_data in _response_200:
            response_200_item = AssaysRunInteractiveResponse200Item.from_dict(
                response_200_item_data
            )

            response_200.append(response_200_item)

        return response_200

    if response.status_code == 400:
        response_400 = AssaysRunInteractiveResponse400.from_dict(response.json())

        return response_400

    if response.status_code == 401:
        response_401 = AssaysRunInteractiveResponse401.from_dict(response.json())

        return response_401

    if response.status_code == 500:
        response_500 = AssaysRunInteractiveResponse500.from_dict(response.json())

        return response_500

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[
    Union[
        AssaysRunInteractiveResponse400,
        AssaysRunInteractiveResponse401,
        AssaysRunInteractiveResponse500,
        list["AssaysRunInteractiveResponse200Item"],
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
    body: AssaysRunInteractiveBody,
) -> Response[
    Union[
        AssaysRunInteractiveResponse400,
        AssaysRunInteractiveResponse401,
        AssaysRunInteractiveResponse500,
        list["AssaysRunInteractiveResponse200Item"],
    ]
]:
    """Run assay interactively

     Runs an assay interactively.

    Args:
        body (AssaysRunInteractiveBody):  Request to run an assay interactively.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[AssaysRunInteractiveResponse400, AssaysRunInteractiveResponse401, AssaysRunInteractiveResponse500, list['AssaysRunInteractiveResponse200Item']]]
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
    body: AssaysRunInteractiveBody,
) -> Optional[
    Union[
        AssaysRunInteractiveResponse400,
        AssaysRunInteractiveResponse401,
        AssaysRunInteractiveResponse500,
        list["AssaysRunInteractiveResponse200Item"],
    ]
]:
    """Run assay interactively

     Runs an assay interactively.

    Args:
        body (AssaysRunInteractiveBody):  Request to run an assay interactively.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[AssaysRunInteractiveResponse400, AssaysRunInteractiveResponse401, AssaysRunInteractiveResponse500, list['AssaysRunInteractiveResponse200Item']]
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: AssaysRunInteractiveBody,
) -> Response[
    Union[
        AssaysRunInteractiveResponse400,
        AssaysRunInteractiveResponse401,
        AssaysRunInteractiveResponse500,
        list["AssaysRunInteractiveResponse200Item"],
    ]
]:
    """Run assay interactively

     Runs an assay interactively.

    Args:
        body (AssaysRunInteractiveBody):  Request to run an assay interactively.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[AssaysRunInteractiveResponse400, AssaysRunInteractiveResponse401, AssaysRunInteractiveResponse500, list['AssaysRunInteractiveResponse200Item']]]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    body: AssaysRunInteractiveBody,
) -> Optional[
    Union[
        AssaysRunInteractiveResponse400,
        AssaysRunInteractiveResponse401,
        AssaysRunInteractiveResponse500,
        list["AssaysRunInteractiveResponse200Item"],
    ]
]:
    """Run assay interactively

     Runs an assay interactively.

    Args:
        body (AssaysRunInteractiveBody):  Request to run an assay interactively.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[AssaysRunInteractiveResponse400, AssaysRunInteractiveResponse401, AssaysRunInteractiveResponse500, list['AssaysRunInteractiveResponse200Item']]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
