from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.score_body import ScoreBody
from ...models.score_response_200 import ScoreResponse200
from ...types import Response


def _get_kwargs(
    *,
    body: ScoreBody,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/v2/api/assays/score",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[ScoreResponse200]:
    if response.status_code == 200:
        response_200 = ScoreResponse200.from_dict(response.json())

        return response_200

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[ScoreResponse200]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: ScoreBody,
) -> Response[ScoreResponse200]:
    r"""Scoring is the process of:

     1. Taking 2 ranges of data
    2. Summarizing them
    3. Using a [`Metric`] to summarize the difference between their Summaries.

    curl -X POST http://localhost:3040/v2/api/assays/score -H 'Authorization: Bearer test' -H 'Content-
    Type: application/json' -d '{\"window\": {\"Stored\": [\"2022-01-06T00:00:00+00:00\",
    \"2022-01-07T00:00:00+00:00\"]}, \"baseline\": {\"Static\": [\"2022-01-01T00:00:00+00:00\",
    \"2022-01-02T00:00:00+00:00\"]}, \"summarizer\": {\"UnivariateContinuous\":
    {\"bin_mode\":{\"Equal\":8},\"aggregation\":\"Density\",\"metric\":\"PSI\",\"bin_weights\":null}}}'

    Args:
        body (ScoreBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ScoreResponse200]
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
    body: ScoreBody,
) -> Optional[ScoreResponse200]:
    r"""Scoring is the process of:

     1. Taking 2 ranges of data
    2. Summarizing them
    3. Using a [`Metric`] to summarize the difference between their Summaries.

    curl -X POST http://localhost:3040/v2/api/assays/score -H 'Authorization: Bearer test' -H 'Content-
    Type: application/json' -d '{\"window\": {\"Stored\": [\"2022-01-06T00:00:00+00:00\",
    \"2022-01-07T00:00:00+00:00\"]}, \"baseline\": {\"Static\": [\"2022-01-01T00:00:00+00:00\",
    \"2022-01-02T00:00:00+00:00\"]}, \"summarizer\": {\"UnivariateContinuous\":
    {\"bin_mode\":{\"Equal\":8},\"aggregation\":\"Density\",\"metric\":\"PSI\",\"bin_weights\":null}}}'

    Args:
        body (ScoreBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ScoreResponse200
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: ScoreBody,
) -> Response[ScoreResponse200]:
    r"""Scoring is the process of:

     1. Taking 2 ranges of data
    2. Summarizing them
    3. Using a [`Metric`] to summarize the difference between their Summaries.

    curl -X POST http://localhost:3040/v2/api/assays/score -H 'Authorization: Bearer test' -H 'Content-
    Type: application/json' -d '{\"window\": {\"Stored\": [\"2022-01-06T00:00:00+00:00\",
    \"2022-01-07T00:00:00+00:00\"]}, \"baseline\": {\"Static\": [\"2022-01-01T00:00:00+00:00\",
    \"2022-01-02T00:00:00+00:00\"]}, \"summarizer\": {\"UnivariateContinuous\":
    {\"bin_mode\":{\"Equal\":8},\"aggregation\":\"Density\",\"metric\":\"PSI\",\"bin_weights\":null}}}'

    Args:
        body (ScoreBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ScoreResponse200]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    body: ScoreBody,
) -> Optional[ScoreResponse200]:
    r"""Scoring is the process of:

     1. Taking 2 ranges of data
    2. Summarizing them
    3. Using a [`Metric`] to summarize the difference between their Summaries.

    curl -X POST http://localhost:3040/v2/api/assays/score -H 'Authorization: Bearer test' -H 'Content-
    Type: application/json' -d '{\"window\": {\"Stored\": [\"2022-01-06T00:00:00+00:00\",
    \"2022-01-07T00:00:00+00:00\"]}, \"baseline\": {\"Static\": [\"2022-01-01T00:00:00+00:00\",
    \"2022-01-02T00:00:00+00:00\"]}, \"summarizer\": {\"UnivariateContinuous\":
    {\"bin_mode\":{\"Equal\":8},\"aggregation\":\"Density\",\"metric\":\"PSI\",\"bin_weights\":null}}}'

    Args:
        body (ScoreBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ScoreResponse200
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
