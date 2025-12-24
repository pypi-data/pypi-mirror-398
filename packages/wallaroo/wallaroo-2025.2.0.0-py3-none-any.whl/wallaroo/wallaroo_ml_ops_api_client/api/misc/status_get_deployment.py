from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.status_get_deployment_body import StatusGetDeploymentBody
from ...models.status_get_deployment_response_200 import StatusGetDeploymentResponse200
from ...models.status_get_deployment_response_400 import StatusGetDeploymentResponse400
from ...models.status_get_deployment_response_401 import StatusGetDeploymentResponse401
from ...models.status_get_deployment_response_500 import StatusGetDeploymentResponse500
from ...types import Response


def _get_kwargs(
    *,
    body: StatusGetDeploymentBody,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/v1/api/status/get_deployment",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[
    Union[
        StatusGetDeploymentResponse200,
        StatusGetDeploymentResponse400,
        StatusGetDeploymentResponse401,
        StatusGetDeploymentResponse500,
    ]
]:
    if response.status_code == 200:
        response_200 = StatusGetDeploymentResponse200.from_dict(response.json())

        return response_200

    if response.status_code == 400:
        response_400 = StatusGetDeploymentResponse400.from_dict(response.json())

        return response_400

    if response.status_code == 401:
        response_401 = StatusGetDeploymentResponse401.from_dict(response.json())

        return response_401

    if response.status_code == 500:
        response_500 = StatusGetDeploymentResponse500.from_dict(response.json())

        return response_500

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[
    Union[
        StatusGetDeploymentResponse200,
        StatusGetDeploymentResponse400,
        StatusGetDeploymentResponse401,
        StatusGetDeploymentResponse500,
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
    body: StatusGetDeploymentBody,
) -> Response[
    Union[
        StatusGetDeploymentResponse200,
        StatusGetDeploymentResponse400,
        StatusGetDeploymentResponse401,
        StatusGetDeploymentResponse500,
    ]
]:
    """Deployment statuses are made up of the engine pods and the statuses of the pipelines and models in
    each of the running engines

     Gets the full status of a deployment.

    Args:
        body (StatusGetDeploymentBody):  Request for deployment status.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[StatusGetDeploymentResponse200, StatusGetDeploymentResponse400, StatusGetDeploymentResponse401, StatusGetDeploymentResponse500]]
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
    body: StatusGetDeploymentBody,
) -> Optional[
    Union[
        StatusGetDeploymentResponse200,
        StatusGetDeploymentResponse400,
        StatusGetDeploymentResponse401,
        StatusGetDeploymentResponse500,
    ]
]:
    """Deployment statuses are made up of the engine pods and the statuses of the pipelines and models in
    each of the running engines

     Gets the full status of a deployment.

    Args:
        body (StatusGetDeploymentBody):  Request for deployment status.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[StatusGetDeploymentResponse200, StatusGetDeploymentResponse400, StatusGetDeploymentResponse401, StatusGetDeploymentResponse500]
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: StatusGetDeploymentBody,
) -> Response[
    Union[
        StatusGetDeploymentResponse200,
        StatusGetDeploymentResponse400,
        StatusGetDeploymentResponse401,
        StatusGetDeploymentResponse500,
    ]
]:
    """Deployment statuses are made up of the engine pods and the statuses of the pipelines and models in
    each of the running engines

     Gets the full status of a deployment.

    Args:
        body (StatusGetDeploymentBody):  Request for deployment status.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[StatusGetDeploymentResponse200, StatusGetDeploymentResponse400, StatusGetDeploymentResponse401, StatusGetDeploymentResponse500]]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    body: StatusGetDeploymentBody,
) -> Optional[
    Union[
        StatusGetDeploymentResponse200,
        StatusGetDeploymentResponse400,
        StatusGetDeploymentResponse401,
        StatusGetDeploymentResponse500,
    ]
]:
    """Deployment statuses are made up of the engine pods and the statuses of the pipelines and models in
    each of the running engines

     Gets the full status of a deployment.

    Args:
        body (StatusGetDeploymentBody):  Request for deployment status.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[StatusGetDeploymentResponse200, StatusGetDeploymentResponse400, StatusGetDeploymentResponse401, StatusGetDeploymentResponse500]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
