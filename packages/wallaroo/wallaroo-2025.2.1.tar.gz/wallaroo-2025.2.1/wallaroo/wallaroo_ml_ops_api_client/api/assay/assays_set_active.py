from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.assays_set_active_body import AssaysSetActiveBody
from ...models.assays_set_active_response_200 import AssaysSetActiveResponse200
from ...models.assays_set_active_response_400 import AssaysSetActiveResponse400
from ...models.assays_set_active_response_401 import AssaysSetActiveResponse401
from ...models.assays_set_active_response_500 import AssaysSetActiveResponse500
from ...types import Response


def _get_kwargs(
    *,
    body: AssaysSetActiveBody,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/v1/api/assays/set_active",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[
    Union[
        AssaysSetActiveResponse200,
        AssaysSetActiveResponse400,
        AssaysSetActiveResponse401,
        AssaysSetActiveResponse500,
    ]
]:
    if response.status_code == 200:
        response_200 = AssaysSetActiveResponse200.from_dict(response.json())

        return response_200

    if response.status_code == 400:
        response_400 = AssaysSetActiveResponse400.from_dict(response.json())

        return response_400

    if response.status_code == 401:
        response_401 = AssaysSetActiveResponse401.from_dict(response.json())

        return response_401

    if response.status_code == 500:
        response_500 = AssaysSetActiveResponse500.from_dict(response.json())

        return response_500

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[
    Union[
        AssaysSetActiveResponse200,
        AssaysSetActiveResponse400,
        AssaysSetActiveResponse401,
        AssaysSetActiveResponse500,
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
    body: AssaysSetActiveBody,
) -> Response[
    Union[
        AssaysSetActiveResponse200,
        AssaysSetActiveResponse400,
        AssaysSetActiveResponse401,
        AssaysSetActiveResponse500,
    ]
]:
    """Activate or deactivate assay

     Activates or deactivates an assay.

    Args:
        body (AssaysSetActiveBody):  Request to activate or deactivate an assay.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[AssaysSetActiveResponse200, AssaysSetActiveResponse400, AssaysSetActiveResponse401, AssaysSetActiveResponse500]]
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
    body: AssaysSetActiveBody,
) -> Optional[
    Union[
        AssaysSetActiveResponse200,
        AssaysSetActiveResponse400,
        AssaysSetActiveResponse401,
        AssaysSetActiveResponse500,
    ]
]:
    """Activate or deactivate assay

     Activates or deactivates an assay.

    Args:
        body (AssaysSetActiveBody):  Request to activate or deactivate an assay.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[AssaysSetActiveResponse200, AssaysSetActiveResponse400, AssaysSetActiveResponse401, AssaysSetActiveResponse500]
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: AssaysSetActiveBody,
) -> Response[
    Union[
        AssaysSetActiveResponse200,
        AssaysSetActiveResponse400,
        AssaysSetActiveResponse401,
        AssaysSetActiveResponse500,
    ]
]:
    """Activate or deactivate assay

     Activates or deactivates an assay.

    Args:
        body (AssaysSetActiveBody):  Request to activate or deactivate an assay.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[AssaysSetActiveResponse200, AssaysSetActiveResponse400, AssaysSetActiveResponse401, AssaysSetActiveResponse500]]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    body: AssaysSetActiveBody,
) -> Optional[
    Union[
        AssaysSetActiveResponse200,
        AssaysSetActiveResponse400,
        AssaysSetActiveResponse401,
        AssaysSetActiveResponse500,
    ]
]:
    """Activate or deactivate assay

     Activates or deactivates an assay.

    Args:
        body (AssaysSetActiveBody):  Request to activate or deactivate an assay.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[AssaysSetActiveResponse200, AssaysSetActiveResponse400, AssaysSetActiveResponse401, AssaysSetActiveResponse500]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
