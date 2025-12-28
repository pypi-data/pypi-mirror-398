from datetime import datetime

import pandas as pd
import pytest

from wallaroo.assays_v2.preview_result import PreviewResult, PreviewResultList
from wallaroo.wallaroo_ml_ops_api_client.models import (
    PreviewResult as MLOpsPreviewResult,
)


@pytest.fixture
def preview_result(
    assay_v2_builder, window_start_end, scores, preview_window_summaries
):
    result = MLOpsPreviewResult(
        id="some-assay-result-id",
        assay_id="12345678-1234-1234-1234-123456789abc",
        analyzed_at=datetime.fromisoformat("2023-01-01T01:00:00+00:00"),
        elapsed_millis=1000,
        pipeline_id=1,
        window_end=datetime.fromisoformat(window_start_end[1]),
        scores=scores,
        summaries=preview_window_summaries,
        workspace_id=1,
        workspace_name="some-workspace-name",
    )
    return PreviewResult(result, assay_v2_builder)


@pytest.fixture
def preview_result_list(preview_result, assay_v2_builder):
    return PreviewResultList([preview_result], assay_v2_builder)


def test_init_preview_result(mocker, assay_v2_builder, window_start_end):
    result = MLOpsPreviewResult(
        id="some-assay-result-id",
        assay_id="12345678-1234-1234-1234-123456789abc",
        analyzed_at=datetime.fromisoformat("2023-01-01T01:00:00+00:00"),
        elapsed_millis=1000,
        pipeline_id=1,
        window_end=datetime.fromisoformat(window_start_end[1]),
        scores={"out.variable.0": mocker.Mock()},
        summaries={"out.variable.0": mocker.Mock()},
        workspace_id=1,
        workspace_name="some-workspace-name",
    )
    preview_result = PreviewResult(result, assay_v2_builder)

    assert preview_result.raw == result
    assert preview_result.window_end == result.window_end
    assert preview_result.scores == result.scores
    assert preview_result.summaries == result.summaries
    assert preview_result._iopath == "out.variable.0"
    assert (
        preview_result._baseline_summary
        == assay_v2_builder.baseline.summary["out.variable.0"]
    )
    assert preview_result._window_summary == result.summaries["out.variable.0"]
    assert preview_result._summarizer == assay_v2_builder.summarizer


def test_compare_basic_stats(preview_result, baseline_start_end, window_start_end):
    expected_df = pd.DataFrame(
        {
            "Baseline": [
                500.0,
                5.0,
                3.0,
                3.0,
                1.0,
                1.58,
                baseline_start_end[0],
                baseline_start_end[1],
            ],
            "Window": [
                1000.0,
                6.0,
                4.0,
                4.0,
                2.0,
                1.58,
                window_start_end[0],
                window_start_end[1],
            ],
            "diff": [500.0, 1.0, 1.0, 1.0, 1.0, 0.0, None, None],
            "pct_diff": [100.0, 20.0, 33.333333, 33.333333, 100.0, 0.0, None, None],
        },
        index=["count", "max", "mean", "median", "min", "std", "start", "end"],
    )
    expected_df["pct_diff"] = expected_df["pct_diff"].astype("O")
    expected_df["diff"] = expected_df["diff"].astype("O")

    df = preview_result.compare_basic_stats()

    pd.testing.assert_frame_equal(df.sort_index(axis=1), expected_df.sort_index(axis=1))


def test_compare_bins(preview_result, labels, window_edges):
    expected_df = pd.DataFrame(
        {
            "baseline_edges": [0, 1, 2, 3, 4],
            "baseline_labels": labels,
            "baseline_values": [1, 2, 3, 4, 5],
            "window_edges": window_edges,
            "window_labels": labels,
            "window_values": [2, 3, 4, 5, 6],
            "diff_in_pcts": [1, 1, 1, 1, 1],
        }
    )

    df = preview_result.compare_bins()

    pd.testing.assert_frame_equal(df.sort_index(axis=1), expected_df.sort_index(axis=1))


def test_to_df_row(
    preview_result,
    window_start_end,
    baseline_summaries,
    preview_window_summaries,
    targeting,
    scores,
    assay_v2_builder,
):
    expected_row = {
        "id": "some-assay-result-id",
        "assay_id": "12345678-1234-1234-1234-123456789abc",
        "window_start": window_start_end[0],
        "analyzed_at": datetime.fromisoformat("2023-01-01T01:00:00+00:00"),
        "elapsed_millis": 1000,
        "pipeline_id": 1,
        "workspace_id": 1,
        "workspace_name": "some-workspace-name",
        "baseline_summary": baseline_summaries["out.variable.0"].to_dict(),
        "window_summary": preview_window_summaries["out.variable.0"].to_dict(),
        "warning_threshold": targeting.iopath[0].thresholds.warning,
        "alert_threshold": targeting.iopath[0].thresholds.alert,
        "bin_index": None,
        "summarizer": assay_v2_builder.summarizer.to_dict(),
        "status": "Warning",
        "created_at": None,
        "score": scores["out.variable.0"].score,
        "scores": scores["out.variable.0"].scores,
    }

    row = preview_result.to_df_row()

    assert row == expected_row


def test_init_preview_result_list(
    preview_result_list, preview_result, assay_v2_builder
):
    assert isinstance(preview_result_list, PreviewResultList)
    assert preview_result_list.parent_assay == assay_v2_builder
    assert len(preview_result_list) == 1
    assert preview_result_list[0] == preview_result


def test_to_dataframe(
    preview_window_summaries,
    preview_result_list,
    window_start_end,
    scores,
    targeting,
):
    expected_df = pd.DataFrame(
        {
            "id": ["some-assay-result-id"],
            "assay_id": ["12345678-1234-1234-1234-123456789abc"],
            "assay_name": ["some-pipeline-name assay"],
            "iopath": ["out.variable.0"],
            "pipeline_id": [1],
            "pipeline_name": ["some-pipeline-name"],
            "workspace_id": [1],
            "workspace_name": ["some-workspace-name"],
            "score": [scores["out.variable.0"].score],
            "start": [datetime.fromisoformat(window_start_end[0])],
            "min": [preview_window_summaries["out.variable.0"].statistics.min_],
            "max": [preview_window_summaries["out.variable.0"].statistics.max_],
            "mean": [preview_window_summaries["out.variable.0"].statistics.mean],
            "median": [preview_window_summaries["out.variable.0"].statistics.median],
            "std": [preview_window_summaries["out.variable.0"].statistics.std],
            "status": ["Warning"],
            "warning_threshold": [targeting.iopath[0].thresholds.warning],
            "alert_threshold": [targeting.iopath[0].thresholds.alert],
        }
    )

    df = preview_result_list.to_dataframe()

    pd.testing.assert_frame_equal(df.sort_index(axis=1), expected_df.sort_index(axis=1))


def test_to_full_dataframe(
    preview_window_summaries,
    baseline_summaries,
    preview_result_list,
    window_start_end,
    baseline_start_end,
    targeting,
    scores,
):
    expected_df = pd.DataFrame(
        {
            "id": ["some-assay-result-id"],
            "assay_id": ["12345678-1234-1234-1234-123456789abc"],
            "window_start": [window_start_end[0]],
            "analyzed_at": [datetime.fromisoformat("2023-01-01T01:00:00+00:00")],
            "elapsed_millis": [1000],
            "pipeline_id": [1],
            "workspace_id": [1],
            "workspace_name": ["some-workspace-name"],
            "baseline_summary_aggregated_values_0": [
                baseline_summaries["out.variable.0"].aggregated_values[0]
            ],
            "baseline_summary_aggregated_values_1": [
                baseline_summaries["out.variable.0"].aggregated_values[1]
            ],
            "baseline_summary_aggregated_values_2": [
                baseline_summaries["out.variable.0"].aggregated_values[2]
            ],
            "baseline_summary_aggregated_values_3": [
                baseline_summaries["out.variable.0"].aggregated_values[3]
            ],
            "baseline_summary_aggregated_values_4": [
                baseline_summaries["out.variable.0"].aggregated_values[4]
            ],
            "baseline_summary_aggregation": ["Cumulative"],
            "baseline_summary_bins_edges_0": [
                baseline_summaries["out.variable.0"].bins.edges[0]
            ],
            "baseline_summary_bins_edges_1": [
                baseline_summaries["out.variable.0"].bins.edges[1]
            ],
            "baseline_summary_bins_edges_2": [
                baseline_summaries["out.variable.0"].bins.edges[2]
            ],
            "baseline_summary_bins_edges_3": [
                baseline_summaries["out.variable.0"].bins.edges[3]
            ],
            "baseline_summary_bins_edges_4": [
                baseline_summaries["out.variable.0"].bins.edges[4]
            ],
            "baseline_summary_bins_labels_0": [
                baseline_summaries["out.variable.0"].bins.labels[0]
            ],
            "baseline_summary_bins_labels_1": [
                baseline_summaries["out.variable.0"].bins.labels[1]
            ],
            "baseline_summary_bins_labels_2": [
                baseline_summaries["out.variable.0"].bins.labels[2]
            ],
            "baseline_summary_bins_labels_3": [
                baseline_summaries["out.variable.0"].bins.labels[3]
            ],
            "baseline_summary_bins_labels_4": [
                baseline_summaries["out.variable.0"].bins.labels[4]
            ],
            "baseline_summary_bins_mode_Equal": [
                baseline_summaries["out.variable.0"].bins.mode.equal
            ],
            "baseline_summary_name": ["out.variable.0"],
            "baseline_summary_statistics_count": [
                baseline_summaries["out.variable.0"].statistics.count
            ],
            "baseline_summary_statistics_max": [
                baseline_summaries["out.variable.0"].statistics.max_
            ],
            "baseline_summary_statistics_mean": [
                baseline_summaries["out.variable.0"].statistics.mean
            ],
            "baseline_summary_statistics_median": [
                baseline_summaries["out.variable.0"].statistics.median
            ],
            "baseline_summary_statistics_min": [
                baseline_summaries["out.variable.0"].statistics.min_
            ],
            "baseline_summary_statistics_std": [
                baseline_summaries["out.variable.0"].statistics.std
            ],
            "baseline_summary_end": [baseline_start_end[1]],
            "baseline_summary_start": [baseline_start_end[0]],
            "window_summary_aggregated_values_0": [
                preview_window_summaries["out.variable.0"].aggregated_values[0]
            ],
            "window_summary_aggregated_values_1": [
                preview_window_summaries["out.variable.0"].aggregated_values[1]
            ],
            "window_summary_aggregated_values_2": [
                preview_window_summaries["out.variable.0"].aggregated_values[2]
            ],
            "window_summary_aggregated_values_3": [
                preview_window_summaries["out.variable.0"].aggregated_values[3]
            ],
            "window_summary_aggregated_values_4": [
                preview_window_summaries["out.variable.0"].aggregated_values[4]
            ],
            "window_summary_bins_edges_0": [
                preview_window_summaries["out.variable.0"].bins.edges[0]
            ],
            "window_summary_bins_edges_1": [
                preview_window_summaries["out.variable.0"].bins.edges[1]
            ],
            "window_summary_bins_edges_2": [
                preview_window_summaries["out.variable.0"].bins.edges[2]
            ],
            "window_summary_bins_edges_3": [
                preview_window_summaries["out.variable.0"].bins.edges[3]
            ],
            "window_summary_bins_edges_4": [
                preview_window_summaries["out.variable.0"].bins.edges[4]
            ],
            "window_summary_bins_labels_0": [
                preview_window_summaries["out.variable.0"].bins.labels[0]
            ],
            "window_summary_bins_labels_1": [
                preview_window_summaries["out.variable.0"].bins.labels[1]
            ],
            "window_summary_bins_labels_2": [
                preview_window_summaries["out.variable.0"].bins.labels[2]
            ],
            "window_summary_bins_labels_3": [
                preview_window_summaries["out.variable.0"].bins.labels[3]
            ],
            "window_summary_bins_labels_4": [
                preview_window_summaries["out.variable.0"].bins.labels[4]
            ],
            "window_summary_bins_mode_Equal": [
                preview_window_summaries["out.variable.0"].bins.mode.equal
            ],
            "window_summary_statistics_count": [
                preview_window_summaries["out.variable.0"].statistics.count
            ],
            "window_summary_statistics_max": [
                preview_window_summaries["out.variable.0"].statistics.max_
            ],
            "window_summary_statistics_mean": [
                preview_window_summaries["out.variable.0"].statistics.mean
            ],
            "window_summary_statistics_median": [
                preview_window_summaries["out.variable.0"].statistics.median
            ],
            "window_summary_statistics_min": [
                preview_window_summaries["out.variable.0"].statistics.min_
            ],
            "window_summary_statistics_std": [
                preview_window_summaries["out.variable.0"].statistics.std
            ],
            "window_summary_end": [window_start_end[1]],
            "window_summary_start": [window_start_end[0]],
            "warning_threshold": [targeting.iopath[0].thresholds.warning],
            "alert_threshold": [targeting.iopath[0].thresholds.alert],
            "score": [scores["out.variable.0"].score],
            "scores_0": [scores["out.variable.0"].scores[0]],
            "scores_1": [scores["out.variable.0"].scores[1]],
            "scores_2": [scores["out.variable.0"].scores[2]],
            "scores_3": [scores["out.variable.0"].scores[3]],
            "scores_4": [scores["out.variable.0"].scores[4]],
            "bin_index": [None],
            "summarizer_UnivariateContinuous_aggregation": [
                baseline_summaries["out.variable.0"].aggregation
            ],
            "summarizer_UnivariateContinuous_bin_mode_Equal": [
                baseline_summaries["out.variable.0"].bins.mode.equal
            ],
            "summarizer_UnivariateContinuous_metric": ["MaxDiff"],
            "summarizer_UnivariateContinuous_bin_weights": [None],
            "status": ["Warning"],
            "created_at": [None],
        }
    )

    df = preview_result_list.to_full_dataframe()

    pd.testing.assert_frame_equal(df.sort_index(axis=1), expected_df.sort_index(axis=1))
