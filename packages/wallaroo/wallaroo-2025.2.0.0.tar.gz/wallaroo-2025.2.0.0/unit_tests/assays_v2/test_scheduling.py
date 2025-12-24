from datetime import datetime, timezone

import pytest
from freezegun import freeze_time

from wallaroo.assay_config import AssayConfig as V1AssayConfig
from wallaroo.assays_v2.scheduling import Scheduling
from wallaroo.wallaroo_ml_ops_api_client.models import (
    IntervalUnit,
    PGInterval,
    RunFrequencyType1 as MLOpsSimpleRunFrequency,
)


@pytest.mark.parametrize(
    "interval, expected_quantity, expected_unit",
    [
        ("5 minutes", 5, IntervalUnit.MINUTE),
        ("5 hours", 5, IntervalUnit.HOUR),
        ("5 days", 5, IntervalUnit.DAY),
        ("5 weeks", 5, IntervalUnit.WEEK),
    ],
)
def test_from_v1_config_if_interval_provided(
    mocker, interval, expected_quantity, expected_unit
):
    start = datetime(2023, 1, 1, tzinfo=timezone.utc)
    mock_v1_config = mocker.Mock(
        spec=V1AssayConfig,
        window=mocker.Mock(interval=interval, start=start),
    )
    mock_v1_config.run_until = None

    result = Scheduling._from_v1_config(mock_v1_config, None)

    assert isinstance(result, Scheduling)
    assert result.first_run == start
    assert isinstance(result.run_frequency, MLOpsSimpleRunFrequency)
    assert result.run_frequency.simple_run_frequency == PGInterval(
        quantity=expected_quantity, unit=expected_unit
    )


def test_from_v1_config_if_width_provided(mocker):
    start = datetime(2023, 1, 1, tzinfo=timezone.utc)
    mock_v1_config = mocker.Mock(
        spec=V1AssayConfig,
        window=mocker.Mock(
            interval=None,
            width="5 minutes",
            start=start,
        ),
        run_until=None,
    )

    result = Scheduling._from_v1_config(mock_v1_config, None)

    assert result.first_run == start
    assert result.run_frequency.simple_run_frequency == PGInterval(
        quantity=5, unit=IntervalUnit.MINUTE
    )


def test_from_v1_config_raise_error_if_interval_invalid(mocker):
    start = datetime(2023, 1, 1, tzinfo=timezone.utc)
    mock_v1_config = mocker.Mock(
        spec=V1AssayConfig,
        window=mocker.Mock(interval="invalid value", width="5 minutes", start=start),
        run_until=None,
    )

    with pytest.raises(
        Exception,
        match="Failed to parse the run frequency for this assay with interval: `invalid value`",
    ):
        _ = Scheduling._from_v1_config(mock_v1_config, None)


@freeze_time("2023-01-01")
def test_from_v1_config_if_window_start_not_provided(mocker):
    expected_first_run = datetime(2023, 1, 1, tzinfo=timezone.utc)
    mock_v1_config = mocker.Mock(
        spec=V1AssayConfig,
        window=mocker.Mock(interval=None, width="5 minutes", start=None),
        run_until=None,
    )

    result = Scheduling._from_v1_config(mock_v1_config, None)

    assert result.first_run == expected_first_run
