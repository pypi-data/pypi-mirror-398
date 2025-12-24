from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.field_tagged_summaries import FieldTaggedSummaries
from ...models.preview_baseline_binning_body import PreviewBaselineBinningBody
from ...types import Response


def _get_kwargs(
    *,
    body: PreviewBaselineBinningBody,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/v2/api/assays/preview_baseline_binning",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[FieldTaggedSummaries]:
    if response.status_code == 200:
        response_200 = FieldTaggedSummaries.from_dict(response.json())

        return response_200

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[FieldTaggedSummaries]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: PreviewBaselineBinningBody,
) -> Response[FieldTaggedSummaries]:
    r"""Previewing a Baseline is requesting a histogram that shows how

     the baseline's data would be binned for comparison to windows.
    The minimal response is therefore a dataframe:
    _|    bins    | count
    0| (-Inf, 0.1]| 5
    1| (0.1, 0.24]| 10
    2| (0.24, 0.4]| 11
    3| (0.4, 0.45]| 6
    4| (0.45, Inf)| 2

    Bins may also have descriptive labels, such as quantiles, or user-provided labels.
    The first and last bins, to infinity, are designated as outliers.

    curl -X POST localhost:3040/v2/api/assays/preview_baseline_binning -H 'Authorization: Bearer test'
    -H 'Content-Type: application/json' -d '{\"baseline\": {\"Static\": [\"2023-07-16T15:40:28+00:00\",
    \"2023-07-26T15:40:28+00:00\"]}}'
    curl -X POST localhost:3040/v2/api/assays/preview_baseline_binning -H 'Authorization: Bearer test'
    -H 'Content-Type: application/json' -d '{\"baseline\": {\"Summary\": {\"bins\": {\"mode\":
    {\"Equal\": 10}, \"edges\": [],\"labels\": []},\"aggregated_values\": [],\"aggregation\":
    \"Edges\",\"statistics\": {\"count\": 21,\"min\": 1,\"max\": 21,\"mean\": 10,\"median\": 10,\"std\":
    2}}}}'
    curl -X POST http://localhost:3040/v2/api/assays/preview_baseline_binning -H 'Authorization: Bearer
    test' -H 'Content-Type: application/json' -d '{\"baseline\": {\"Static\":
    [\"2022-01-06T00:00:00+00:00\", \"2022-01-07T00:00:00+00:00\"]}}' | jq .
    curl -X POST http://localhost:3040/v2/api/assays/preview_baseline_binning -H 'Authorization: Bearer
    test' -H 'Content-Type: application/json' -d '{\"baseline\": {\"Static\":
    [\"2022-01-06T00:00:00+00:00\", \"2022-01-07T00:00:00+00:00\"]}, \"targeting\": {\"data_origin\":
    {\"pipeline_name\": \"modelinsightse2e05246\", \"workspace_id\": 1}, \"iopath\": [{\"field\":
    \"out.dense_2\", \"index\": 9}]}, \"summarizer\": {\"UnivariateContinuous\": {\"bin_mode\":
    {\"Equal\": 8},\"aggregation\": \"Density\",\"metric\": \"PSI\",\"bin_weights\": null}}}'

    Args:
        body (PreviewBaselineBinningBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[FieldTaggedSummaries]
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
    body: PreviewBaselineBinningBody,
) -> Optional[FieldTaggedSummaries]:
    r"""Previewing a Baseline is requesting a histogram that shows how

     the baseline's data would be binned for comparison to windows.
    The minimal response is therefore a dataframe:
    _|    bins    | count
    0| (-Inf, 0.1]| 5
    1| (0.1, 0.24]| 10
    2| (0.24, 0.4]| 11
    3| (0.4, 0.45]| 6
    4| (0.45, Inf)| 2

    Bins may also have descriptive labels, such as quantiles, or user-provided labels.
    The first and last bins, to infinity, are designated as outliers.

    curl -X POST localhost:3040/v2/api/assays/preview_baseline_binning -H 'Authorization: Bearer test'
    -H 'Content-Type: application/json' -d '{\"baseline\": {\"Static\": [\"2023-07-16T15:40:28+00:00\",
    \"2023-07-26T15:40:28+00:00\"]}}'
    curl -X POST localhost:3040/v2/api/assays/preview_baseline_binning -H 'Authorization: Bearer test'
    -H 'Content-Type: application/json' -d '{\"baseline\": {\"Summary\": {\"bins\": {\"mode\":
    {\"Equal\": 10}, \"edges\": [],\"labels\": []},\"aggregated_values\": [],\"aggregation\":
    \"Edges\",\"statistics\": {\"count\": 21,\"min\": 1,\"max\": 21,\"mean\": 10,\"median\": 10,\"std\":
    2}}}}'
    curl -X POST http://localhost:3040/v2/api/assays/preview_baseline_binning -H 'Authorization: Bearer
    test' -H 'Content-Type: application/json' -d '{\"baseline\": {\"Static\":
    [\"2022-01-06T00:00:00+00:00\", \"2022-01-07T00:00:00+00:00\"]}}' | jq .
    curl -X POST http://localhost:3040/v2/api/assays/preview_baseline_binning -H 'Authorization: Bearer
    test' -H 'Content-Type: application/json' -d '{\"baseline\": {\"Static\":
    [\"2022-01-06T00:00:00+00:00\", \"2022-01-07T00:00:00+00:00\"]}, \"targeting\": {\"data_origin\":
    {\"pipeline_name\": \"modelinsightse2e05246\", \"workspace_id\": 1}, \"iopath\": [{\"field\":
    \"out.dense_2\", \"index\": 9}]}, \"summarizer\": {\"UnivariateContinuous\": {\"bin_mode\":
    {\"Equal\": 8},\"aggregation\": \"Density\",\"metric\": \"PSI\",\"bin_weights\": null}}}'

    Args:
        body (PreviewBaselineBinningBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        FieldTaggedSummaries
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: PreviewBaselineBinningBody,
) -> Response[FieldTaggedSummaries]:
    r"""Previewing a Baseline is requesting a histogram that shows how

     the baseline's data would be binned for comparison to windows.
    The minimal response is therefore a dataframe:
    _|    bins    | count
    0| (-Inf, 0.1]| 5
    1| (0.1, 0.24]| 10
    2| (0.24, 0.4]| 11
    3| (0.4, 0.45]| 6
    4| (0.45, Inf)| 2

    Bins may also have descriptive labels, such as quantiles, or user-provided labels.
    The first and last bins, to infinity, are designated as outliers.

    curl -X POST localhost:3040/v2/api/assays/preview_baseline_binning -H 'Authorization: Bearer test'
    -H 'Content-Type: application/json' -d '{\"baseline\": {\"Static\": [\"2023-07-16T15:40:28+00:00\",
    \"2023-07-26T15:40:28+00:00\"]}}'
    curl -X POST localhost:3040/v2/api/assays/preview_baseline_binning -H 'Authorization: Bearer test'
    -H 'Content-Type: application/json' -d '{\"baseline\": {\"Summary\": {\"bins\": {\"mode\":
    {\"Equal\": 10}, \"edges\": [],\"labels\": []},\"aggregated_values\": [],\"aggregation\":
    \"Edges\",\"statistics\": {\"count\": 21,\"min\": 1,\"max\": 21,\"mean\": 10,\"median\": 10,\"std\":
    2}}}}'
    curl -X POST http://localhost:3040/v2/api/assays/preview_baseline_binning -H 'Authorization: Bearer
    test' -H 'Content-Type: application/json' -d '{\"baseline\": {\"Static\":
    [\"2022-01-06T00:00:00+00:00\", \"2022-01-07T00:00:00+00:00\"]}}' | jq .
    curl -X POST http://localhost:3040/v2/api/assays/preview_baseline_binning -H 'Authorization: Bearer
    test' -H 'Content-Type: application/json' -d '{\"baseline\": {\"Static\":
    [\"2022-01-06T00:00:00+00:00\", \"2022-01-07T00:00:00+00:00\"]}, \"targeting\": {\"data_origin\":
    {\"pipeline_name\": \"modelinsightse2e05246\", \"workspace_id\": 1}, \"iopath\": [{\"field\":
    \"out.dense_2\", \"index\": 9}]}, \"summarizer\": {\"UnivariateContinuous\": {\"bin_mode\":
    {\"Equal\": 8},\"aggregation\": \"Density\",\"metric\": \"PSI\",\"bin_weights\": null}}}'

    Args:
        body (PreviewBaselineBinningBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[FieldTaggedSummaries]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    body: PreviewBaselineBinningBody,
) -> Optional[FieldTaggedSummaries]:
    r"""Previewing a Baseline is requesting a histogram that shows how

     the baseline's data would be binned for comparison to windows.
    The minimal response is therefore a dataframe:
    _|    bins    | count
    0| (-Inf, 0.1]| 5
    1| (0.1, 0.24]| 10
    2| (0.24, 0.4]| 11
    3| (0.4, 0.45]| 6
    4| (0.45, Inf)| 2

    Bins may also have descriptive labels, such as quantiles, or user-provided labels.
    The first and last bins, to infinity, are designated as outliers.

    curl -X POST localhost:3040/v2/api/assays/preview_baseline_binning -H 'Authorization: Bearer test'
    -H 'Content-Type: application/json' -d '{\"baseline\": {\"Static\": [\"2023-07-16T15:40:28+00:00\",
    \"2023-07-26T15:40:28+00:00\"]}}'
    curl -X POST localhost:3040/v2/api/assays/preview_baseline_binning -H 'Authorization: Bearer test'
    -H 'Content-Type: application/json' -d '{\"baseline\": {\"Summary\": {\"bins\": {\"mode\":
    {\"Equal\": 10}, \"edges\": [],\"labels\": []},\"aggregated_values\": [],\"aggregation\":
    \"Edges\",\"statistics\": {\"count\": 21,\"min\": 1,\"max\": 21,\"mean\": 10,\"median\": 10,\"std\":
    2}}}}'
    curl -X POST http://localhost:3040/v2/api/assays/preview_baseline_binning -H 'Authorization: Bearer
    test' -H 'Content-Type: application/json' -d '{\"baseline\": {\"Static\":
    [\"2022-01-06T00:00:00+00:00\", \"2022-01-07T00:00:00+00:00\"]}}' | jq .
    curl -X POST http://localhost:3040/v2/api/assays/preview_baseline_binning -H 'Authorization: Bearer
    test' -H 'Content-Type: application/json' -d '{\"baseline\": {\"Static\":
    [\"2022-01-06T00:00:00+00:00\", \"2022-01-07T00:00:00+00:00\"]}, \"targeting\": {\"data_origin\":
    {\"pipeline_name\": \"modelinsightse2e05246\", \"workspace_id\": 1}, \"iopath\": [{\"field\":
    \"out.dense_2\", \"index\": 9}]}, \"summarizer\": {\"UnivariateContinuous\": {\"bin_mode\":
    {\"Equal\": 8},\"aggregation\": \"Density\",\"metric\": \"PSI\",\"bin_weights\": null}}}'

    Args:
        body (PreviewBaselineBinningBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        FieldTaggedSummaries
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
