from datetime import datetime, timezone

import pandas as pd
import pytest

from wallaroo.assays_v2 import AssayV2
from wallaroo.assays_v2.assay_result_v2 import AssayResultsList


@pytest.fixture
def assay_results_list(assay_result_v2):
    return AssayResultsList([assay_result_v2], assay_result_v2.parent_assay)


def test_init_assay_result_v2(
    assay_result_v2, baseline_summaries, mlops_assay_result_v2, assay_window_summaries
):
    assert isinstance(assay_result_v2.parent_assay, AssayV2)
    assert assay_result_v2.raw == mlops_assay_result_v2
    assert assay_result_v2.v1_iopath == "out.variable.0"
    assert assay_result_v2._baseline_summary == baseline_summaries["out.variable.0"]
    assert assay_result_v2._window_summary == assay_window_summaries["out.variable.0"]


def test_compare_basic_stats(
    assay_result_v2,
    baseline_start_end,
    baseline_stats,
    window_start_end,
    window_stats,
):
    data = {
        "Baseline": [
            baseline_stats.count,
            baseline_stats.max_,
            baseline_stats.mean,
            baseline_stats.median,
            baseline_stats.min_,
            baseline_stats.std,
            baseline_start_end[0],
            baseline_start_end[1],
        ],
        "Window": [
            window_stats.count,
            window_stats.max_,
            window_stats.mean,
            window_stats.median,
            window_stats.min_,
            window_stats.std,
            window_start_end[0],
            window_start_end[1],
        ],
        "diff": [500.0, 1.0, 1.0, 1.0, 1.0, 0.0, None, None],
        "pct_diff": [100.0, 20.0, 33.333333, 33.333333, 100.0, 0.0, None, None],
    }
    index = ["count", "max", "mean", "median", "min", "std", "start", "end"]
    expected_df = pd.DataFrame(data, index=index)
    expected_df["pct_diff"] = expected_df["pct_diff"].astype("O")
    expected_df["diff"] = expected_df["diff"].astype("O")

    df = assay_result_v2.compare_basic_stats()

    pd.testing.assert_frame_equal(df.sort_index(axis=1), expected_df.sort_index(axis=1))


def test_init_assay_results_list(assay_results_list, assay_result_v2, assay_v2):
    assert isinstance(assay_results_list, AssayResultsList)
    assert assay_results_list.parent_assay == assay_v2
    assert len(assay_results_list) == 1
    assert assay_results_list[0] == assay_result_v2


def test_to_df_row(
    assay_result_v2,
    window_start_end,
    baseline_summaries,
    assay_window_summaries,
    targeting,
    scores,
    assay_v2_builder,
):
    expected_row = {
        "id": "some-assay-result-id",
        "assay_id": "12345678-1234-1234-1234-123456789abc",
        "window_start": datetime.fromisoformat(window_start_end[0]),
        "analyzed_at": datetime(2023, 1, 1, 1, 0, tzinfo=timezone.utc),
        "elapsed_millis": 1000,
        "pipeline_id": 1,
        "workspace_id": 1,
        "workspace_name": "some-workspace-name",
        "baseline_summary": baseline_summaries["out.variable.0"].to_dict(),
        "window_summary": assay_window_summaries["out.variable.0"].to_dict(),
        "warning_threshold": targeting.iopath[0].thresholds.warning,
        "alert_threshold": targeting.iopath[0].thresholds.alert,
        "bin_index": None,
        "summarizer": assay_v2_builder.summarizer.to_dict(),
        "status": "Warning",
        "created_at": datetime(2023, 1, 1, 1, 0, tzinfo=timezone.utc),
        "score": scores["out.variable.0"].score,
        "scores": scores["out.variable.0"].scores,
    }

    row = assay_result_v2.to_df_row()

    assert row == expected_row


def test_to_dataframe(
    assay_window_summaries,
    assay_results_list,
    window_start_end,
    scores,
    targeting,
):
    expected_df = pd.DataFrame(
        {
            "id": ["some-assay-result-id"],
            "assay_id": ["12345678-1234-1234-1234-123456789abc"],
            "assay_name": ["some-assay-name"],
            "iopath": ["out.variable.0"],
            "pipeline_id": [1],
            "pipeline_name": ["some-pipeline-name"],
            "workspace_id": [1],
            "workspace_name": ["some-workspace-name"],
            "score": [scores["out.variable.0"].score],
            "start": [window_start_end[0]],
            "min": [assay_window_summaries["out.variable.0"].statistics.min_],
            "max": [assay_window_summaries["out.variable.0"].statistics.max_],
            "mean": [assay_window_summaries["out.variable.0"].statistics.mean],
            "median": [assay_window_summaries["out.variable.0"].statistics.median],
            "std": [assay_window_summaries["out.variable.0"].statistics.std],
            "status": ["Warning"],
            "warning_threshold": [targeting.iopath[0].thresholds.warning],
            "alert_threshold": [targeting.iopath[0].thresholds.alert],
        }
    )

    df = assay_results_list.to_dataframe()

    pd.testing.assert_frame_equal(df.sort_index(axis=1), expected_df.sort_index(axis=1))


def test_to_full_dataframe(
    assay_window_summaries,
    baseline_summaries,
    assay_results_list,
    targeting,
    scores,
    window_start_end,
    baseline_start_end,
):
    expected_df = pd.DataFrame(
        {
            "id": ["some-assay-result-id"],
            "assay_id": ["12345678-1234-1234-1234-123456789abc"],
            "window_start": [datetime.fromisoformat(window_start_end[0])],
            "analyzed_at": [datetime(2023, 1, 1, 1, 0, tzinfo=timezone.utc)],
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
                assay_window_summaries["out.variable.0"].aggregated_values[0]
            ],
            "window_summary_aggregated_values_1": [
                assay_window_summaries["out.variable.0"].aggregated_values[1]
            ],
            "window_summary_aggregated_values_2": [
                assay_window_summaries["out.variable.0"].aggregated_values[2]
            ],
            "window_summary_aggregated_values_3": [
                assay_window_summaries["out.variable.0"].aggregated_values[3]
            ],
            "window_summary_aggregated_values_4": [
                assay_window_summaries["out.variable.0"].aggregated_values[4]
            ],
            "window_summary_bins_edges_0": [
                assay_window_summaries["out.variable.0"].bins.edges[0]
            ],
            "window_summary_bins_edges_1": [
                assay_window_summaries["out.variable.0"].bins.edges[1]
            ],
            "window_summary_bins_edges_2": [
                assay_window_summaries["out.variable.0"].bins.edges[2]
            ],
            "window_summary_bins_edges_3": [
                assay_window_summaries["out.variable.0"].bins.edges[3]
            ],
            "window_summary_bins_edges_4": [
                assay_window_summaries["out.variable.0"].bins.edges[4]
            ],
            "window_summary_bins_labels_0": [
                assay_window_summaries["out.variable.0"].bins.labels[0]
            ],
            "window_summary_bins_labels_1": [
                assay_window_summaries["out.variable.0"].bins.labels[1]
            ],
            "window_summary_bins_labels_2": [
                assay_window_summaries["out.variable.0"].bins.labels[2]
            ],
            "window_summary_bins_labels_3": [
                assay_window_summaries["out.variable.0"].bins.labels[3]
            ],
            "window_summary_bins_labels_4": [
                assay_window_summaries["out.variable.0"].bins.labels[4]
            ],
            "window_summary_bins_mode_Equal": [
                assay_window_summaries["out.variable.0"].bins.mode.equal
            ],
            "window_summary_statistics_count": [
                assay_window_summaries["out.variable.0"].statistics.count
            ],
            "window_summary_statistics_max": [
                assay_window_summaries["out.variable.0"].statistics.max_
            ],
            "window_summary_statistics_mean": [
                assay_window_summaries["out.variable.0"].statistics.mean
            ],
            "window_summary_statistics_median": [
                assay_window_summaries["out.variable.0"].statistics.median
            ],
            "window_summary_statistics_min": [
                assay_window_summaries["out.variable.0"].statistics.min_
            ],
            "window_summary_statistics_std": [
                assay_window_summaries["out.variable.0"].statistics.std
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
            "created_at": [datetime(2023, 1, 1, 1, 0, tzinfo=timezone.utc)],
            "window_summary_name": ["out.variable.0"],
            "window_summary_aggregation": ["Cumulative"],
        }
    )

    df = assay_results_list.to_full_dataframe()

    pd.testing.assert_frame_equal(df.sort_index(axis=1), expected_df.sort_index(axis=1))
