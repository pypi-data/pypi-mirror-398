from datetime import datetime

import pytest
from freezegun import freeze_time

from wallaroo.assay_config import (
    Aggregation as V1Aggregation,
    AssayConfig,
    BinMode as V1BinMode,
    Metric as V1Metric,
    StaticBaseline as V1StaticBaseline,
    UnivariateContinousSummarizerConfig,
    WindowConfig,
)
from wallaroo.assays_v2 import AssayV2, AssayV2Builder
from wallaroo.assays_v2.baseline import StaticBaseline, SummaryBaseline
from wallaroo.assays_v2.preview_result import PreviewResultList
from wallaroo.assays_v2.scheduling import Scheduling
from wallaroo.assays_v2.summarizer import Summarizer
from wallaroo.assays_v2.targeting import Targeting
from wallaroo.wallaroo_ml_ops_api_client.api.assays.preview import (
    PreviewBody,
)
from wallaroo.wallaroo_ml_ops_api_client.models import (
    Aggregation,
    BinModeType0,
    BinModeType1,
    BinModeType2,
    DataOrigin,
    DataPath,
    IntervalUnit,
    Metric,
    PGInterval,
    PreviewResult as MLOpsPreviewResult,
    RollingWindow,
    RunFrequencyType1 as MLOpsSimpleRunFrequency,
    ScheduleBody,
    Thresholds,
    UnivariateContinuous,
    WindowWidthDuration,
)


@pytest.fixture
def mlops_preview_result(window_start_end, scores, preview_window_summaries):
    return MLOpsPreviewResult(
        analyzed_at=datetime.fromisoformat("2024-01-02T00:00:00"),
        assay_id="12345678-1234-1234-1234-123456789abc",
        elapsed_millis=1000,
        id="some-assay-result-id",
        pipeline_id=1,
        scores=scores,
        summaries=preview_window_summaries,
        window_end=datetime.fromisoformat(window_start_end[1]),
        workspace_id=1,
        workspace_name="some-workspace-name",
    )


@freeze_time("2024-01-01T00:00:00")
def test_init(client, mocker):
    mocker.patch(
        "wallaroo.workspace.Workspace.name",
        return_value="some-workspace-name",
    )
    builder = AssayV2Builder(client, 1, "some-pipeline-name", 1)

    assert isinstance(builder, AssayV2Builder)
    assert builder.client == client
    assert builder.name == "some-pipeline-name assay"
    assert isinstance(builder.targeting, Targeting)
    assert builder.targeting.data_origin.pipeline_name == "some-pipeline-name"
    assert builder.targeting.data_origin.workspace_id == 1
    assert builder.baseline is None
    assert isinstance(builder.scheduling, Scheduling)
    assert (
        builder.scheduling.first_run.isoformat()
        == datetime.now().astimezone().isoformat()
    )
    assert builder.scheduling.run_frequency == MLOpsSimpleRunFrequency(
        PGInterval(1, IntervalUnit.DAY)
    )
    assert builder.summarizer is None
    assert builder.bin_mode is None
    assert builder.window is None
    assert builder.bin_weights is None


@pytest.mark.parametrize(
    "baseline, targeting, metric, aggregation, bin_mode, expected_error",
    [
        (
            None,
            Targeting(None, []),
            None,
            None,
            None,
            "No baseline is configured. See `set_baseline`",
        ),
        (
            object(),
            Targeting(None, []),
            None,
            None,
            None,
            "No monitoring paths are configured. See `add_monitoring`",
        ),
        (
            object(),
            Targeting(None, [object()]),
            None,
            None,
            None,
            "No metric is configured.",
        ),
        (
            object(),
            Targeting(None, [object()]),
            object(),
            None,
            None,
            "No aggregation is configured",
        ),
        (
            object(),
            Targeting(None, [object()]),
            object(),
            object(),
            None,
            "No binning mode is configured",
        ),
    ],
)
def test_validate(
    assay_v2_builder,
    baseline,
    targeting,
    metric,
    aggregation,
    bin_mode,
    expected_error,
):
    assay_v2_builder.baseline = baseline
    assay_v2_builder.targeting = targeting
    assay_v2_builder.metric = metric
    assay_v2_builder.aggregation = aggregation
    assay_v2_builder.bin_mode = bin_mode

    with pytest.raises(Exception, match=expected_error):
        assay_v2_builder._validate()


@pytest.fixture
def assay_v2_builder_from_v1_config(
    client,
    baseline_summaries,
    baseline_stats,
    window_start_end,
    mocker,
):
    baseline_stats = baseline_stats.to_dict()
    baseline_stats["max_"], baseline_stats["min_"] = (
        baseline_stats.pop("max"),
        baseline_stats.pop("min"),
    )
    mocker.patch(
        "wallaroo.workspace.Workspace.name",
        return_value="some-workspace-name",
    )
    assay_v1_config = AssayConfig(
        client=client,
        name="some-pipeline-name assay",
        pipeline_id=1,
        pipeline_name="some-pipeline-name",
        active=True,
        status="some-status",
        baseline=V1StaticBaseline(
            **baseline_stats,
            edges=baseline_summaries["out.variable.0"].bins.edges,
            edge_names=baseline_summaries["out.variable.0"].bins.labels,
            aggregated_values=baseline_summaries["out.variable.0"].aggregated_values,
            aggregation=baseline_summaries["out.variable.0"].aggregation,
            start=baseline_summaries["out.variable.0"].start,
            end=baseline_summaries["out.variable.0"].end,
        ),
        window=WindowConfig(
            pipeline_name="some-pipeline-name",
            width="2 minutes",
            model_name="some-model-name",
            start=datetime.fromisoformat(window_start_end[0]),
            interval="2 minutes",
            path="output variable 0",
            workspace_id=1,
            locations=[],
        ),
        summarizer=UnivariateContinousSummarizerConfig(
            bin_mode=V1BinMode.EQUAL,
            aggregation=baseline_summaries["out.variable.0"].aggregation,
            metric=Metric.MAXDIFF,
            num_bins=baseline_summaries["out.variable.0"].bins.mode.equal,
            bin_weights=None,
            bin_width=None,
            provided_edges=None,
            add_outlier_edges=True,
        ),
        warning_threshold=0.8,
        alert_threshold=0.9,
        run_until=datetime.fromisoformat("2024-01-02T00:00:00"),
        workspace_id=1,
        workspace_name="some-workspace-name",
    )
    return AssayV2Builder._from_v1_config(assay_v1_config)


def test_from_v1_config(
    client,
    baseline_summaries,
    assay_v2_builder_from_v1_config,
):
    assert isinstance(assay_v2_builder_from_v1_config, AssayV2Builder)
    assert assay_v2_builder_from_v1_config.client == client
    assert isinstance(assay_v2_builder_from_v1_config.targeting, Targeting)
    assert assay_v2_builder_from_v1_config.targeting.data_origin == DataOrigin(
        pipeline_id=1,
        pipeline_name="some-pipeline-name",
        workspace_id=1,
        workspace_name="some-workspace-name",
        model_id="some-model-name",
        locations=None,
    )
    assert len(assay_v2_builder_from_v1_config.targeting.iopath) == 1
    assert assay_v2_builder_from_v1_config.targeting.iopath[0] == DataPath(
        field="out.variable",
        indexes=[0],
        thresholds=Thresholds(alert=0.9, warning=0.8),
    )
    assert isinstance(assay_v2_builder_from_v1_config.baseline, SummaryBaseline)
    assert assay_v2_builder_from_v1_config.baseline.summary == baseline_summaries
    assert isinstance(assay_v2_builder_from_v1_config.summarizer, Summarizer)
    assert assay_v2_builder_from_v1_config.summarizer == Summarizer(
        univariate_continuous=UnivariateContinuous(
            metric=Metric.MAXDIFF,
            bin_mode=BinModeType1(5),
            aggregation=Aggregation.CUMULATIVE,
            bin_weights=None,
        )
    )
    assert assay_v2_builder_from_v1_config.bin_mode == BinModeType1(5)
    assert isinstance(assay_v2_builder_from_v1_config.window, RollingWindow)
    assert assay_v2_builder_from_v1_config.window.width == WindowWidthDuration(
        seconds=120
    )
    assert assay_v2_builder_from_v1_config.metric == Metric.MAXDIFF
    assert assay_v2_builder_from_v1_config.aggregation == Aggregation.CUMULATIVE
    assert assay_v2_builder_from_v1_config.bin_weights is None


def test_build(client, assay_v2_builder_from_v1_config, mocker):
    mock_return = mocker.Mock()
    mock_return.parsed = "12345678-1234-1234-1234-123456789abc"
    mock_schedule = mocker.patch(
        "wallaroo.assays_v2.assay_v2_builder.sync_detailed_schedule",
        return_value=mock_return,
    )
    mock_schedule_body = mocker.spy(ScheduleBody, "__init__")
    mocker.patch(
        "wallaroo.object.Object._rehydrate",
        return_value=None,
    )

    assay_v2 = assay_v2_builder_from_v1_config.build()

    assert isinstance(assay_v2, AssayV2)
    assert assay_v2.id == "12345678-1234-1234-1234-123456789abc"
    assert assay_v2._client == client
    mock_schedule.assert_called_once()
    mock_schedule_body.assert_called_once_with(
        mocker.ANY,
        name=assay_v2_builder_from_v1_config.name,
        baseline=assay_v2_builder_from_v1_config.baseline,
        scheduling=assay_v2_builder_from_v1_config.scheduling,
        summarizer=assay_v2_builder_from_v1_config.summarizer,
        targeting=assay_v2_builder_from_v1_config.targeting,
        window=assay_v2_builder_from_v1_config.window,
    )
    assert mock_schedule.call_args[1]["client"] == client.mlops()
    assert (
        mock_schedule.call_args[1]["body"].name == assay_v2_builder_from_v1_config.name
    )
    assert (
        mock_schedule.call_args[1]["body"].baseline
        == assay_v2_builder_from_v1_config.baseline
    )
    assert (
        mock_schedule.call_args[1]["body"].scheduling
        == assay_v2_builder_from_v1_config.scheduling
    )
    assert (
        mock_schedule.call_args[1]["body"].summarizer
        == assay_v2_builder_from_v1_config.summarizer
    )
    assert (
        mock_schedule.call_args[1]["body"].targeting
        == assay_v2_builder_from_v1_config.targeting
    )
    assert (
        mock_schedule.call_args[1]["body"].window
        == assay_v2_builder_from_v1_config.window
    )


def test_set_name(assay_v2_builder_from_v1_config):
    assert assay_v2_builder_from_v1_config.name == "some-pipeline-name assay"
    assert (
        assay_v2_builder_from_v1_config.set_name("some-new-name").name
        == "some-new-name"
    )


def test_set_pipeline(assay_v2_builder_from_v1_config):
    assay_v2_builder_from_v1_config.set_pipeline("some-new-pipeline-name", 2)

    assert (
        assay_v2_builder_from_v1_config.targeting.data_origin.pipeline_name
        == "some-new-pipeline-name"
    )
    assert assay_v2_builder_from_v1_config.targeting.data_origin.workspace_id == 2


def test_set_model(assay_v2_builder_from_v1_config):
    assay_v2_builder_from_v1_config = assay_v2_builder_from_v1_config.set_model(
        "some-new-model-name"
    )

    assert (
        assay_v2_builder_from_v1_config.targeting.data_origin.model_id
        == "some-new-model-name"
    )


def test_add_monitoring(assay_v2_builder_from_v1_config):
    assay_v2_builder_from_v1_config = assay_v2_builder_from_v1_config.add_monitoring(
        "out.variable2", [1], 0.1, 0.2
    )

    assert assay_v2_builder_from_v1_config.targeting.iopath == [
        DataPath(
            field="out.variable",
            indexes=[0],
            thresholds=Thresholds(alert=0.9, warning=0.8),
        ),
        DataPath(
            field="out.variable2",
            indexes=[1],
            thresholds=Thresholds(alert=0.2, warning=0.1),
        ),
    ]


def test_set_monitoring(assay_v2_builder_from_v1_config):
    assay_v2_builder_from_v1_config = assay_v2_builder_from_v1_config.set_monitoring(
        "out.variable", [0], 0.1, 0.2
    )

    assert assay_v2_builder_from_v1_config.targeting.iopath == [
        DataPath(
            field="out.variable",
            indexes=[0],
            thresholds=Thresholds(alert=0.2, warning=0.1),
        ),
    ]


def test_set_baseline(assay_v2_builder_from_v1_config):
    start, end = datetime.now(), datetime.now()
    assay_v2_builder_from_v1_config = assay_v2_builder_from_v1_config.set_baseline(
        start, end
    )

    assert assay_v2_builder_from_v1_config.baseline == StaticBaseline(
        [
            start,
            end,
        ]
    )


def test_set_baseline_if_window_is_none(assay_v2_builder_from_v1_config):
    start, end = datetime.now(), datetime.now()
    assay_v2_builder_from_v1_config.window = None
    assay_v2_builder_from_v1_config = assay_v2_builder_from_v1_config.set_baseline(
        start, end
    )

    assert assay_v2_builder_from_v1_config.baseline == StaticBaseline(
        [
            start,
            end,
        ]
    )
    assert isinstance(assay_v2_builder_from_v1_config.window, RollingWindow)
    assert assay_v2_builder_from_v1_config.window.width == WindowWidthDuration(
        seconds=0
    )


def test_set_window_width(assay_v2_builder_from_v1_config):
    assay_v2_builder_from_v1_config = assay_v2_builder_from_v1_config.set_window_width(
        10
    )

    assert isinstance(assay_v2_builder_from_v1_config.window, RollingWindow)
    assert assay_v2_builder_from_v1_config.window.width == WindowWidthDuration(
        seconds=10
    )


def test_set_first_run(assay_v2_builder_from_v1_config):
    first_run = datetime.now()
    assay_v2_builder_from_v1_config = assay_v2_builder_from_v1_config.set_first_run(
        first_run
    )

    assert (
        assay_v2_builder_from_v1_config.scheduling.first_run == first_run.astimezone()
    )


def test_daily(assay_v2_builder_from_v1_config):
    assay_v2_builder_from_v1_config = assay_v2_builder_from_v1_config.daily(2)

    assert (
        assay_v2_builder_from_v1_config.scheduling.run_frequency
        == MLOpsSimpleRunFrequency(PGInterval(2, IntervalUnit.DAY))
    )


def test_hourly(assay_v2_builder_from_v1_config):
    assay_v2_builder_from_v1_config = assay_v2_builder_from_v1_config.hourly(2)

    assert (
        assay_v2_builder_from_v1_config.scheduling.run_frequency
        == MLOpsSimpleRunFrequency(PGInterval(2, IntervalUnit.HOUR))
    )


def test_weekly(assay_v2_builder_from_v1_config):
    assay_v2_builder_from_v1_config = assay_v2_builder_from_v1_config.weekly()

    assert (
        assay_v2_builder_from_v1_config.scheduling.run_frequency
        == MLOpsSimpleRunFrequency(PGInterval(1, IntervalUnit.WEEK))
    )


def test_minutely(assay_v2_builder_from_v1_config):
    assay_v2_builder_from_v1_config = assay_v2_builder_from_v1_config.minutely(2)

    assert (
        assay_v2_builder_from_v1_config.scheduling.run_frequency
        == MLOpsSimpleRunFrequency(PGInterval(2, IntervalUnit.MINUTE))
    )


def test_days_of_data(assay_v2_builder_from_v1_config):
    assay_v2_builder_from_v1_config = assay_v2_builder_from_v1_config.days_of_data(2)

    assert isinstance(assay_v2_builder_from_v1_config.window, RollingWindow)
    assert assay_v2_builder_from_v1_config.window.width == WindowWidthDuration(
        seconds=172800
    )


def test_minutes_of_data(assay_v2_builder_from_v1_config):
    assay_v2_builder_from_v1_config = assay_v2_builder_from_v1_config.minutes_of_data(2)

    assert isinstance(assay_v2_builder_from_v1_config.window, RollingWindow)
    assert assay_v2_builder_from_v1_config.window.width == WindowWidthDuration(
        seconds=120
    )


def test_hours_of_data(assay_v2_builder_from_v1_config):
    assay_v2_builder_from_v1_config = assay_v2_builder_from_v1_config.hours_of_data(2)

    assert isinstance(assay_v2_builder_from_v1_config.window, RollingWindow)
    assert assay_v2_builder_from_v1_config.window.width == WindowWidthDuration(
        seconds=7200
    )


def test_weeks_of_data(assay_v2_builder_from_v1_config):
    assay_v2_builder_from_v1_config = assay_v2_builder_from_v1_config.weeks_of_data(2)

    assert isinstance(assay_v2_builder_from_v1_config.window, RollingWindow)
    assert assay_v2_builder_from_v1_config.window.width == WindowWidthDuration(
        seconds=1209600
    )


def test_cumulative_aggregation(assay_v2_builder_from_v1_config):
    assay_v2_builder_from_v1_config = (
        assay_v2_builder_from_v1_config.cumulative_aggregation()
    )

    assert assay_v2_builder_from_v1_config.aggregation == Aggregation.CUMULATIVE


def test_density_aggregation(assay_v2_builder_from_v1_config):
    assay_v2_builder_from_v1_config = (
        assay_v2_builder_from_v1_config.density_aggregation()
    )

    assert assay_v2_builder_from_v1_config.aggregation == Aggregation.DENSITY


def test_edge_aggregation(assay_v2_builder_from_v1_config):
    assay_v2_builder_from_v1_config = assay_v2_builder_from_v1_config.edge_aggregation()

    assert assay_v2_builder_from_v1_config.aggregation == Aggregation.EDGES


def test_max_diff_metric(assay_v2_builder_from_v1_config):
    assay_v2_builder_from_v1_config = assay_v2_builder_from_v1_config.max_diff_metric()

    assert assay_v2_builder_from_v1_config.metric == Metric.MAXDIFF


def test_psi_metric(assay_v2_builder_from_v1_config):
    assay_v2_builder_from_v1_config = assay_v2_builder_from_v1_config.psi_metric()

    assert assay_v2_builder_from_v1_config.metric == Metric.PSI


def test_sum_diff_metric(assay_v2_builder_from_v1_config):
    assay_v2_builder_from_v1_config = assay_v2_builder_from_v1_config.sum_diff_metric()


def test_no_bins(assay_v2_builder_from_v1_config):
    assay_v2_builder_from_v1_config = assay_v2_builder_from_v1_config.no_bins()

    assert assay_v2_builder_from_v1_config.bin_mode == BinModeType0.NONE


def test_equal_bins(assay_v2_builder_from_v1_config):
    assay_v2_builder_from_v1_config = assay_v2_builder_from_v1_config.equal_bins(2)

    assert isinstance(assay_v2_builder_from_v1_config.bin_mode, BinModeType1)
    assert assay_v2_builder_from_v1_config.bin_mode.equal == 2


def test_quantile_bins(assay_v2_builder_from_v1_config):
    assay_v2_builder_from_v1_config = assay_v2_builder_from_v1_config.quantile_bins(2)

    assert isinstance(assay_v2_builder_from_v1_config.bin_mode, BinModeType2)
    assert assay_v2_builder_from_v1_config.bin_mode.quantile == 2


def test_set_bin_weights(assay_v2_builder_from_v1_config):
    assay_v2_builder_from_v1_config = assay_v2_builder_from_v1_config.set_bin_weights(
        [0.1, 0.2, 0.3, 0.4, 0.5]
    )

    assert assay_v2_builder_from_v1_config.bin_weights == [0.1, 0.2, 0.3, 0.4, 0.5]


@pytest.mark.parametrize(
    "aggregation, expected_aggregation",
    [
        (Aggregation.EDGES, Aggregation.EDGES),
        (Aggregation.DENSITY, Aggregation.DENSITY),
        (Aggregation.CUMULATIVE, Aggregation.CUMULATIVE),
        (V1Aggregation.EDGES, Aggregation.EDGES),
        (V1Aggregation.DENSITY, Aggregation.DENSITY),
        (V1Aggregation.CUMULATIVE, Aggregation.CUMULATIVE),
        ("edges", Aggregation.EDGES),
        ("density", Aggregation.DENSITY),
        ("cumulative", Aggregation.CUMULATIVE),
    ],
)
def test_set_aggregation(
    assay_v2_builder_from_v1_config, aggregation, expected_aggregation
):
    assay_v2_builder_from_v1_config = assay_v2_builder_from_v1_config.set_aggregation(
        aggregation
    )

    assert assay_v2_builder_from_v1_config.aggregation == expected_aggregation


@pytest.mark.parametrize(
    "metric, expected_metric",
    [
        (Metric.MAXDIFF, Metric.MAXDIFF),
        (Metric.SUMDIFF, Metric.SUMDIFF),
        (Metric.PSI, Metric.PSI),
        (V1Metric.MAXDIFF, Metric.MAXDIFF),
        (V1Metric.SUMDIFF, Metric.SUMDIFF),
        (V1Metric.PSI, Metric.PSI),
        ("maxdiff", Metric.MAXDIFF),
        ("psi", Metric.PSI),
        ("sumdiff", Metric.SUMDIFF),
    ],
)
def test_set_metric(assay_v2_builder_from_v1_config, metric, expected_metric):
    assay_v2_builder_from_v1_config = assay_v2_builder_from_v1_config.set_metric(metric)

    assert assay_v2_builder_from_v1_config.metric == expected_metric


def test_set_locations(assay_v2_builder_from_v1_config):
    assay_v2_builder_from_v1_config = assay_v2_builder_from_v1_config.set_locations(
        ["some-location"]
    )

    assert assay_v2_builder_from_v1_config.targeting.data_origin.locations == [
        "some-location"
    ]


def test_add_locations(assay_v2_builder_from_v1_config):
    # locations are set to UNSET by default
    assay_v2_builder_from_v1_config = assay_v2_builder_from_v1_config.set_locations(
        ["some-location"]
    )
    assay_v2_builder_from_v1_config = assay_v2_builder_from_v1_config.add_locations(
        "some-other-location"
    )

    assert assay_v2_builder_from_v1_config.targeting.data_origin.locations == [
        "some-location",
        "some-other-location",
    ]


def test_get_iopath(assay_v2_builder_from_v1_config):
    assert assay_v2_builder_from_v1_config._get_iopath() == "out.variable.0"


def test_preview(assay_v2_builder_from_v1_config, mlops_preview_result, mocker):
    start = datetime.now()
    end = datetime.now()
    mock_return = mocker.Mock()
    mock_return.parsed = [mlops_preview_result]
    mock_preview = mocker.patch(
        "wallaroo.assays_v2.assay_v2_builder.sync_detailed_preview",
        return_value=mock_return,
    )
    mock_preview_body = mocker.spy(PreviewBody, "__init__")

    results = assay_v2_builder_from_v1_config.preview(start, end)

    assert assay_v2_builder_from_v1_config.summarizer == Summarizer(
        univariate_continuous=UnivariateContinuous(
            metric=Metric.MAXDIFF,
            bin_mode=BinModeType1(5),
            aggregation=Aggregation.CUMULATIVE,
            bin_weights=None,
        )
    )
    mock_preview_body.assert_called_once_with(
        mocker.ANY,
        baseline=assay_v2_builder_from_v1_config.baseline,
        preview_start=start,
        preview_end=end,
        scheduling=assay_v2_builder_from_v1_config.scheduling,
        summarizer=assay_v2_builder_from_v1_config.summarizer,
        targeting=assay_v2_builder_from_v1_config.targeting,
        window=assay_v2_builder_from_v1_config.window,
    )
    mock_preview.assert_called_once()
    assert (
        mock_preview.call_args[1]["client"]
        == assay_v2_builder_from_v1_config.client.mlops()
    )
    assert (
        mock_preview.call_args[1]["body"].baseline
        == assay_v2_builder_from_v1_config.baseline
    )
    assert mock_preview.call_args[1]["body"].preview_start == start
    assert mock_preview.call_args[1]["body"].preview_end == end
    assert (
        mock_preview.call_args[1]["body"].scheduling
        == assay_v2_builder_from_v1_config.scheduling
    )
    assert (
        mock_preview.call_args[1]["body"].summarizer
        == assay_v2_builder_from_v1_config.summarizer
    )
    assert (
        mock_preview.call_args[1]["body"].targeting
        == assay_v2_builder_from_v1_config.targeting
    )
    assert (
        mock_preview.call_args[1]["body"].window
        == assay_v2_builder_from_v1_config.window
    )
    assert isinstance(results, PreviewResultList)
    assert len(results) == 1
    assert results[0].raw == mlops_preview_result
