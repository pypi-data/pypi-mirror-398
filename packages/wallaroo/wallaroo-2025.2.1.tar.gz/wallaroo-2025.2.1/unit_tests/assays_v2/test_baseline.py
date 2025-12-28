from datetime import datetime, timezone

import pytest

from wallaroo.assay_config import (
    AssayConfig as V1AssayConfig,
    BinMode as V1BinMode,
    CalculatedBaseline as V1CalculatedBaseline,
    FixedBaseline as V1FixedBaseline,
    Metric,
    StaticBaseline as V1StaticBaseline,
    WindowConfig,
)
from wallaroo.assays_v2.baseline import SummaryBaseline, V1Summarizer
from wallaroo.wallaroo_ml_ops_api_client.models import (
    Aggregation,
    BinModeType0,
    BinModeType1,
    BinModeType2,
    BinModeType4,
    FieldTaggedSummaries,
)


@pytest.fixture(scope="module")
def v1_static_baseline():
    return V1StaticBaseline(
        count=3,
        min_=10.0,
        max_=30.0,
        mean=20.0,
        median=20.0,
        std=10.0,
        edges=[1.0, 2.0, None],
        edge_names=["low", "medium", "high"],
        aggregated_values=[10.0, 20.0, 30.0],
        aggregation=Aggregation.CUMULATIVE,
        start=datetime(2024, 1, 1, tzinfo=timezone.utc),
        end=datetime(2024, 1, 1, tzinfo=timezone.utc),
    )


@pytest.fixture(scope="module")
def v1_summarizer():
    return V1Summarizer(
        bin_mode=V1BinMode.PROVIDED,
        aggregation=Aggregation.CUMULATIVE,
        metric=Metric.MAXDIFF,
        num_bins=10,
    )


@pytest.mark.parametrize(
    "bin_mode, expected_bin_mode",
    [
        (V1BinMode.NONE, BinModeType0.NONE),
        (V1BinMode.EQUAL, BinModeType1(10)),
        (V1BinMode.QUANTILE, BinModeType2(10)),
        (V1BinMode.PROVIDED, BinModeType4([1.0, 2.0, "INFINITY"])),
    ],
)
def test_from_v1_summary(bin_mode, expected_bin_mode, v1_static_baseline):
    summarizer = V1Summarizer(
        bin_mode=bin_mode,
        aggregation=Aggregation.CUMULATIVE,
        metric=Metric.MAXDIFF,
        num_bins=10,
    )
    iopath = "out.variable.0"
    expected_start_end = datetime(2024, 1, 1, tzinfo=timezone.utc)

    result = SummaryBaseline.from_v1_summary(v1_static_baseline, summarizer, iopath)

    assert isinstance(result, SummaryBaseline)
    assert isinstance(result.summary, FieldTaggedSummaries)
    assert result.summary[iopath].aggregation == Aggregation.CUMULATIVE
    assert result.summary[iopath].bins.edges == [1.0, 2.0, "INFINITY"]
    assert result.summary[iopath].bins.labels == ["low", "medium", "high"]
    assert result.summary[iopath].bins.mode == expected_bin_mode
    assert result.summary[iopath].aggregated_values == [10.0, 20.0, 30.0]
    assert result.summary[iopath].statistics.count == v1_static_baseline.static.get(
        "count"
    )
    assert result.summary[iopath].statistics.max_ == v1_static_baseline.static.get(
        "max"
    )
    assert result.summary[iopath].statistics.mean == v1_static_baseline.static.get(
        "mean"
    )
    assert result.summary[iopath].statistics.median == v1_static_baseline.static.get(
        "median"
    )
    assert result.summary[iopath].statistics.min_ == v1_static_baseline.static.get(
        "min"
    )
    assert result.summary[iopath].statistics.std == v1_static_baseline.static.get("std")
    assert result.summary[iopath].start == expected_start_end
    assert result.summary[iopath].end == expected_start_end
    assert result.summary[iopath].name == iopath


@pytest.mark.skip("`V1CalculatedBaseline` and `V1FixedBaseline` not supported yet.")
@pytest.mark.parametrize(
    "baseline",
    [
        V1CalculatedBaseline(pipeline_name="pipeline", model_name="model"),
        V1FixedBaseline(pipeline_name="pipeline", model_name="model"),
    ],
)
def test_from_v1_config_if_not_static_baseline(baseline):
    pass


def test_from_v1_config_if_static_baseline(mocker, v1_static_baseline):
    assay_config = mocker.Mock(
        spec=V1AssayConfig,
        baseline=v1_static_baseline,
        summarizer=V1Summarizer(
            bin_mode=V1BinMode.PROVIDED,
            aggregation=Aggregation.CUMULATIVE,
            metric=Metric.MAXDIFF,
            num_bins=10,
        ),
        window=WindowConfig(
            pipeline_name="some-pipeline",
            width="5 minutes",
            path="output variable 0",
            interval="5 minutes",
        ),
    )
    iopath = "out.variable.0"
    expected_start_end = datetime(2024, 1, 1, tzinfo=timezone.utc)

    result = SummaryBaseline._from_v1_config(assay_config)

    assert isinstance(result, SummaryBaseline)
    assert isinstance(result.summary, FieldTaggedSummaries)
    assert result.summary[iopath].name == iopath
    assert result.summary[iopath].statistics.count == v1_static_baseline.static.get(
        "count"
    )
    assert result.summary[iopath].statistics.max_ == v1_static_baseline.static.get(
        "max"
    )
    assert result.summary[iopath].statistics.mean == v1_static_baseline.static.get(
        "mean"
    )
    assert result.summary[iopath].statistics.median == v1_static_baseline.static.get(
        "median"
    )
    assert result.summary[iopath].statistics.min_ == v1_static_baseline.static.get(
        "min"
    )
    assert result.summary[iopath].statistics.std == v1_static_baseline.static.get("std")
    assert result.summary[iopath].start == expected_start_end
    assert result.summary[iopath].end == expected_start_end


def test_from_v1_config_raise_error_if_unknown_baseline_type(mocker):
    assay_config = mocker.Mock(
        spec=V1AssayConfig,
        baseline=mocker.Mock(spec=str),
    )

    with pytest.raises(
        Exception, match="Could not parse unknown V1 baseline type `str`."
    ):
        _ = SummaryBaseline._from_v1_config(assay_config)
