from datetime import datetime, timezone
from uuid import UUID

import pytest

from wallaroo.assays_v2 import AssayV2, AssayV2Builder
from wallaroo.assays_v2.assay_result_v2 import AssayResultsList
from wallaroo.wallaroo_ml_ops_api_client.api.assays.get_results import (
    GetResultsBody,
)


@pytest.fixture
def success_response(mocker):
    mock_return = mocker.Mock()
    mock_return.status_code = 200
    return mock_return


@pytest.fixture
def error_response(mocker):
    mock_return = mocker.Mock()
    mock_return.status_code = 400
    return mock_return


def test_init(assay_v2, client):
    assert isinstance(assay_v2, AssayV2)
    assert assay_v2.id == "12345678-1234-1234-1234-123456789abc"
    assert assay_v2._client == client


def test_results(assay_v2, mocker, mlops_assay_result_v2):
    start, end = datetime.now(tz=timezone.utc), datetime.now(tz=timezone.utc)
    workspace_id = 1
    mock_return = mocker.Mock()
    mock_return.parsed = [mlops_assay_result_v2]
    mock_sync = mocker.patch(
        "wallaroo.assays_v2.assay_v2.sync_detailed_results",
        return_value=mock_return,
    )
    mock_results_body = mocker.spy(GetResultsBody, "__init__")

    results = assay_v2.results(
        start=start,
        end=end,
        include_failures=True,
        workspace_id=1,
    )

    mock_results_body.assert_called_once_with(
        mocker.ANY,
        start=start,
        end=end,
        id=UUID(assay_v2.id),
        workspace_id=workspace_id,
    )
    mock_sync.assert_called_once()
    assert mock_sync.call_args[1]["client"] == assay_v2._client.mlops()
    assert mock_sync.call_args[1]["body"].id == UUID(assay_v2.id)
    assert mock_sync.call_args[1]["body"].start == start
    assert mock_sync.call_args[1]["body"].end == end
    assert mock_sync.call_args[1]["body"].workspace_id == workspace_id
    assert isinstance(results, AssayResultsList)
    assert len(results) == 1
    assert results[0].raw == mlops_assay_result_v2


def test_set_active(assay_v2, mocker):
    mock_return = mocker.Mock()
    mock_return.status_code = 200
    mock_sync = mocker.patch(
        "wallaroo.assays_v2.assay_v2.sync_detailed_set_active",
        return_value=mock_return,
    )

    assay_v2.set_active(True)

    mock_sync.assert_called_once()
    assert mock_sync.call_args[1]["client"] == assay_v2._client.mlops()
    assert mock_sync.call_args[1]["body"].active is True

    assert mock_sync.call_args[1]["body"].assay_id == UUID(assay_v2.id)


@pytest.mark.parametrize(
    "active, expected_verb",
    [(True, "resume"), (False, "pause"), ("some-value", "pause")],
)
def test_set_active_raise_error(
    assay_v2, mocker, active, expected_verb, error_response
):
    mocker.patch(
        "wallaroo.assays_v2.assay_v2.sync_detailed_set_active",
        return_value=error_response,
    )

    with pytest.raises(Exception, match=f"Failed to {expected_verb} assay."):
        assay_v2.set_active(active)


def test_pause(assay_v2, mocker, success_response):
    mock_sync = mocker.patch(
        "wallaroo.assays_v2.assay_v2.sync_detailed_set_active",
        return_value=success_response,
    )

    assay_v2.pause()

    mock_sync.assert_called_once()
    assert mock_sync.call_args[1]["client"] == assay_v2._client.mlops()
    assert mock_sync.call_args[1]["body"].active is False

    assert mock_sync.call_args[1]["body"].assay_id == UUID(assay_v2.id)


def test_resume(assay_v2, mocker, success_response):
    mock_sync = mocker.patch(
        "wallaroo.assays_v2.assay_v2.sync_detailed_set_active",
        return_value=success_response,
    )

    assay_v2.resume()

    mock_sync.assert_called_once()
    assert mock_sync.call_args[1]["client"] == assay_v2._client.mlops()
    assert mock_sync.call_args[1]["body"].active is True

    assert mock_sync.call_args[1]["body"].assay_id == UUID(assay_v2.id)


def test_builder(client, mocker):
    mocker.patch(
        "wallaroo.workspace.Workspace.name",
        return_value="some-workspace-name",
    )
    builder = AssayV2.builder(client, 1, "some-pipeline-name", 1)
    assert isinstance(builder, AssayV2Builder)
    assert builder.client == client
    assert builder.name == "some-pipeline-name assay"
    assert builder.targeting.data_origin.pipeline_id == 1
    assert builder.targeting.data_origin.pipeline_name == "some-pipeline-name"
    assert builder.targeting.data_origin.workspace_id == 1


def test_next_run(assay_v2, mocker):
    mock_return = mocker.Mock()
    mock_return.parsed = "some-value"

    mocker.patch(
        "wallaroo.wallaroo_ml_ops_api_client.api.assays.get_next_run.sync_detailed",
        return_value=mock_return,
    )

    next_run = assay_v2._next_run()
    assert next_run == "some-value"


def test_next_run_raise_error(assay_v2, mocker):
    mock_return = mocker.Mock()
    mock_return.parsed = None
    mock_return.content = "some-error"
    mocker.patch(
        "wallaroo.wallaroo_ml_ops_api_client.api.assays.get_next_run.sync_detailed",
        return_value=mock_return,
    )

    with pytest.raises(Exception, match="some-error"):
        assay_v2._next_run()


def test_get_iopath(assay_v2):
    assert assay_v2._get_iopath() == "out.variable.0"
