from http import HTTPStatus
from typing import Any, Optional, Union, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.assays_run_interactive_baseline_body import (
    AssaysRunInteractiveBaselineBody,
)
from ...models.assays_run_interactive_baseline_response_200_type_0 import (
    AssaysRunInteractiveBaselineResponse200Type0,
)
from ...models.assays_run_interactive_baseline_response_400 import (
    AssaysRunInteractiveBaselineResponse400,
)
from ...models.assays_run_interactive_baseline_response_401 import (
    AssaysRunInteractiveBaselineResponse401,
)
from ...models.assays_run_interactive_baseline_response_500 import (
    AssaysRunInteractiveBaselineResponse500,
)
from ...types import Response


def _get_kwargs(
    *,
    body: AssaysRunInteractiveBaselineBody,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/v1/api/assays/run_interactive_baseline",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[
    Union[
        AssaysRunInteractiveBaselineResponse400,
        AssaysRunInteractiveBaselineResponse401,
        AssaysRunInteractiveBaselineResponse500,
        Union["AssaysRunInteractiveBaselineResponse200Type0", None],
    ]
]:
    if response.status_code == 200:

        def _parse_response_200(
            data: object,
        ) -> Union["AssaysRunInteractiveBaselineResponse200Type0", None]:
            if data is None:
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                response_200_type_0 = (
                    AssaysRunInteractiveBaselineResponse200Type0.from_dict(data)
                )

                return response_200_type_0
            except:  # noqa: E722
                pass
            return cast(
                Union["AssaysRunInteractiveBaselineResponse200Type0", None], data
            )

        response_200 = _parse_response_200(response.json())

        return response_200

    if response.status_code == 400:
        response_400 = AssaysRunInteractiveBaselineResponse400.from_dict(
            response.json()
        )

        return response_400

    if response.status_code == 401:
        response_401 = AssaysRunInteractiveBaselineResponse401.from_dict(
            response.json()
        )

        return response_401

    if response.status_code == 500:
        response_500 = AssaysRunInteractiveBaselineResponse500.from_dict(
            response.json()
        )

        return response_500

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[
    Union[
        AssaysRunInteractiveBaselineResponse400,
        AssaysRunInteractiveBaselineResponse401,
        AssaysRunInteractiveBaselineResponse500,
        Union["AssaysRunInteractiveBaselineResponse200Type0", None],
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
    body: AssaysRunInteractiveBaselineBody,
) -> Response[
    Union[
        AssaysRunInteractiveBaselineResponse400,
        AssaysRunInteractiveBaselineResponse401,
        AssaysRunInteractiveBaselineResponse500,
        Union["AssaysRunInteractiveBaselineResponse200Type0", None],
    ]
]:
    """Create interactive baseline

     Creates an interactive assay baseline.

    Args:
        body (AssaysRunInteractiveBaselineBody):  Request for interactive assay baseline.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[AssaysRunInteractiveBaselineResponse400, AssaysRunInteractiveBaselineResponse401, AssaysRunInteractiveBaselineResponse500, Union['AssaysRunInteractiveBaselineResponse200Type0', None]]]
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
    body: AssaysRunInteractiveBaselineBody,
) -> Optional[
    Union[
        AssaysRunInteractiveBaselineResponse400,
        AssaysRunInteractiveBaselineResponse401,
        AssaysRunInteractiveBaselineResponse500,
        Union["AssaysRunInteractiveBaselineResponse200Type0", None],
    ]
]:
    """Create interactive baseline

     Creates an interactive assay baseline.

    Args:
        body (AssaysRunInteractiveBaselineBody):  Request for interactive assay baseline.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[AssaysRunInteractiveBaselineResponse400, AssaysRunInteractiveBaselineResponse401, AssaysRunInteractiveBaselineResponse500, Union['AssaysRunInteractiveBaselineResponse200Type0', None]]
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: AssaysRunInteractiveBaselineBody,
) -> Response[
    Union[
        AssaysRunInteractiveBaselineResponse400,
        AssaysRunInteractiveBaselineResponse401,
        AssaysRunInteractiveBaselineResponse500,
        Union["AssaysRunInteractiveBaselineResponse200Type0", None],
    ]
]:
    """Create interactive baseline

     Creates an interactive assay baseline.

    Args:
        body (AssaysRunInteractiveBaselineBody):  Request for interactive assay baseline.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[AssaysRunInteractiveBaselineResponse400, AssaysRunInteractiveBaselineResponse401, AssaysRunInteractiveBaselineResponse500, Union['AssaysRunInteractiveBaselineResponse200Type0', None]]]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    body: AssaysRunInteractiveBaselineBody,
) -> Optional[
    Union[
        AssaysRunInteractiveBaselineResponse400,
        AssaysRunInteractiveBaselineResponse401,
        AssaysRunInteractiveBaselineResponse500,
        Union["AssaysRunInteractiveBaselineResponse200Type0", None],
    ]
]:
    """Create interactive baseline

     Creates an interactive assay baseline.

    Args:
        body (AssaysRunInteractiveBaselineBody):  Request for interactive assay baseline.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[AssaysRunInteractiveBaselineResponse400, AssaysRunInteractiveBaselineResponse401, AssaysRunInteractiveBaselineResponse500, Union['AssaysRunInteractiveBaselineResponse200Type0', None]]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
