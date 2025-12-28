"""This module features classes related to an assay v2 result that help with analysis and visualization
for an interactive run."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union, cast

import matplotlib.dates as mdates
import pandas as pd
from matplotlib import pyplot as plt

from wallaroo._inference_decode import dict_list_to_dataframe
from wallaroo.assays_v2.baseline import SummaryBaseline
from wallaroo.assays_v2.summarizer import Summarizer
from wallaroo.wallaroo_ml_ops_api_client.models.aggregation import Aggregation
from wallaroo.wallaroo_ml_ops_api_client.models.bin_mode_type_0 import BinModeType0
from wallaroo.wallaroo_ml_ops_api_client.models.bin_mode_type_1 import BinModeType1
from wallaroo.wallaroo_ml_ops_api_client.models.bin_mode_type_2 import BinModeType2
from wallaroo.wallaroo_ml_ops_api_client.models.bin_mode_type_3 import BinModeType3
from wallaroo.wallaroo_ml_ops_api_client.models.bin_mode_type_4 import BinModeType4
from wallaroo.wallaroo_ml_ops_api_client.models.interval_unit import IntervalUnit
from wallaroo.wallaroo_ml_ops_api_client.models.minimal_summary import (
    MinimalSummary as MLOpsMinimalSummary,
)
from wallaroo.wallaroo_ml_ops_api_client.models.preview_result import (
    PreviewResult as MLOpsPreviewResult,
)
from wallaroo.wallaroo_ml_ops_api_client.models.preview_result_summaries import (
    PreviewResultSummaries,
)
from wallaroo.wallaroo_ml_ops_api_client.models.score_data import ScoreData
from wallaroo.wallaroo_ml_ops_api_client.models.series_summary import SeriesSummary
from wallaroo.wallaroo_ml_ops_api_client.types import Unset

if TYPE_CHECKING:
    from wallaroo.assays_v2.assay_v2_builder import AssayV2Builder


class PreviewResult:
    """This class implements the IAssayAnalysis interface that offers
    a number of methods for analyzing and visualizing assay results
    from an interactive run.

    Attributes:
        - raw: The raw MLOpsPreviewResult object.
        - window_end: The end time of the window.
        - scores: The scores of the window.
        - summaries: The summaries of the window.
    """

    def __init__(self, result: MLOpsPreviewResult, builder: AssayV2Builder) -> None:
        """Initializes the PreviewResult object."""
        self.builder = builder
        self.raw = result
        self.window_end = result.window_end
        self.scores = result.scores
        self.summaries = result.summaries
        self._iopath = builder._get_iopath()
        self._baseline_summary = cast(SummaryBaseline, builder.baseline).summary[
            self._iopath
        ]
        self._window_summary = cast(PreviewResultSummaries, self.summaries)[
            self._iopath
        ]
        self._summarizer = cast(Summarizer, builder.summarizer)

    def chart(self, show_scores: bool = True) -> None:
        """Create a chart showing the bins, values and scores of a preview result.
        `show_scores` will also label each bin with its final weighted (if specified) score.

        :param show_scores: Whether to show the scores for each bin.
        """
        bin_mode = self._summarizer.univariate_continuous.bin_mode
        weighted = isinstance(
            self._summarizer.univariate_continuous.bin_weights,
            List,  # type: ignore[union-attr]
        )
        if isinstance(bin_mode, BinModeType0):
            pass
        elif isinstance(bin_mode, BinModeType1):
            num_bins = bin_mode.equal
            bin_mode_str = "Equal"
        elif isinstance(bin_mode, BinModeType2):
            num_bins = bin_mode.quantile
            bin_mode_str = "Quantile"
        elif isinstance(bin_mode, BinModeType3):
            pass
        elif isinstance(bin_mode, BinModeType4):
            num_bins = len(bin_mode.provided)
            bin_mode_str = "Provided"
        agg = self._summarizer.univariate_continuous.aggregation.value
        baseline_aggregated_values = self._baseline_summary.aggregated_values
        baseline_sample_size = self._baseline_summary.statistics.count
        window_aggregated_values = self._window_summary.aggregated_values
        window_sample_size = self._window_summary.statistics.count
        end = self.window_end
        metric = self._summarizer.univariate_continuous.metric.value
        score_data = cast(ScoreData, self.scores[self._iopath])
        edge_names = self._baseline_summary.bins.labels

        title = f"{num_bins} {bin_mode_str} {agg} {metric}={score_data.score:5.3f} Weighted={weighted} {end}"

        _, ax = plt.subplots()

        if agg == Aggregation.EDGES:
            for n, v in enumerate(baseline_aggregated_values):
                plt.axvline(x=v, color="blue", alpha=0.5)
                plt.text(v, 0, f"e{n}", color="blue")
            for n, v in enumerate(window_aggregated_values):
                plt.axvline(x=v, color="orange", alpha=0.5)
                plt.text(v, 0.1, f"e{n}", color="orange")
        else:
            bar1 = plt.bar(
                edge_names,
                baseline_aggregated_values,
                alpha=0.50,
                label=f"Baseline ({baseline_sample_size})",
            )
            bar2 = plt.bar(
                edge_names,
                window_aggregated_values,
                alpha=0.50,
                label=f"Window ({window_sample_size})",
            )
            if len(edge_names) > 7:
                ax.set_xticklabels(labels=edge_names, rotation=45)

            if show_scores is True:
                for i, (p1, p2) in enumerate(zip(bar1.patches, bar2.patches)):
                    height = max(p1.get_height(), p2.get_height())
                    ax.annotate(
                        f"{score_data.scores[i]:.4f}",
                        (p1.get_x() + p1.get_width() / 2, height),
                        ha="center",
                        va="center",
                        size=9,
                        xytext=(0, 8),
                        textcoords="offset points",
                    )
                # Adjust y-axis limit to accommodate annotations
                y_limit = ax.get_ylim()[1]
                max_height = max(
                    max(baseline_aggregated_values), max(window_aggregated_values)
                )
                new_y_limit = max(y_limit, max_height * 1.15)
                ax.set_ylim(top=new_y_limit)

            # Move legend outside the plot
            ax.legend(loc="upper left", bbox_to_anchor=(1, 1))

        ax.set_title(title)
        plt.xticks(rotation=45)
        # Adjust layout to make room for the legend
        plt.tight_layout()
        plt.subplots_adjust(right=0.85)  # Adjust this value as needed
        plt.show()

    def compare_basic_stats(self) -> pd.DataFrame:
        """Compare basic stats between baseline and window.

        :return pd.DataFrame: A dataframe including stats, start and end times
            for the window against the baseline.
        """
        window_stats = self._get_stats_dict_from_summary(self._window_summary)
        baseline_stats = self._get_stats_dict_from_summary(self._baseline_summary)
        df = pd.concat(
            [
                pd.DataFrame(baseline_stats, index=["Baseline"]),
                pd.DataFrame(window_stats, index=["Window"]),
            ]
        ).reindex(
            columns=["count", "max", "mean", "median", "min", "std", "start", "end"]
        )
        df.loc["diff"] = df.loc["Window"][:-2] - df.loc["Baseline"][:-2]
        df.loc["pct_diff"] = df.loc["diff"][:-2] / df.loc["Baseline"][:-2] * 100.0

        return df.T

    def compare_bins(self) -> pd.DataFrame:
        """Compare bins between baseline and window.

        :return pd.DataFrame: A dataframe including edges, labels and values
            for the window against the baseline.
        """
        window_bins = self._get_bins_dict_from_summary(self._window_summary, "window")
        baseline_bins = self._get_bins_dict_from_summary(
            self._baseline_summary, "baseline"
        )

        window = pd.DataFrame(window_bins)
        baseline = pd.DataFrame(baseline_bins)
        df = pd.concat([baseline, window], axis=1)
        df["diff_in_pcts"] = df["window_values"] - df["baseline_values"]

        return df

    def to_df_row(self) -> Dict[str, Any]:
        """Convert the preview result to a dataframe row.

        :return Dict[str, Any]: A dataframe row.
        """
        warning = self.builder.targeting.iopath[0].thresholds.warning  # type: ignore[union-attr]
        alert = self.builder.targeting.iopath[0].thresholds.alert  # type: ignore[union-attr]
        score_data = cast(ScoreData, self.scores[self._iopath])
        window_summary = self._window_summary.to_dict()
        bin_index = (
            score_data.bin_index
            if not isinstance(score_data.bin_index, Unset)
            else None
        )

        return {
            "id": self.raw.id,
            "assay_id": self.raw.assay_id,
            "window_start": window_summary["start"],
            "analyzed_at": self.raw.analyzed_at,
            "elapsed_millis": self.raw.elapsed_millis,
            "pipeline_id": self.raw.pipeline_id,
            "workspace_id": self.raw.workspace_id,
            "workspace_name": self.raw.workspace_name,
            "baseline_summary": self._baseline_summary.to_dict(),
            "window_summary": window_summary,
            "warning_threshold": warning,
            "alert_threshold": alert,
            "bin_index": bin_index,
            "summarizer": self._summarizer.to_dict(),
            "status": self._calculate_status(
                score_data.score,
                warning,  # type: ignore[arg-type]
                alert,  # type: ignore[arg-type]
            ),
            "created_at": None,
            "score": score_data.score,
            "scores": score_data.scores,
        }

    @staticmethod
    def _calculate_status(
        score: float, warning: Optional[float], alert: Optional[float]
    ) -> str:
        if alert is not None and score >= alert:
            return "Alert"
        elif warning is not None and score >= warning:
            return "Warning"
        else:
            return "Ok"

    @staticmethod
    def _get_stats_dict_from_summary(
        summary: Union[MLOpsMinimalSummary, SeriesSummary],
    ) -> Dict[str, Any]:
        """A helper function to extract statistics-related data from a summary object.

        :param summary: The summary object to extract statistics from.

        :return Dict[str, Any]: A dictionary containing statistics-related data.

        Example:

        {
            count: 100,
            min: 0.0,
            max: 1.0,
            mean: 0.5,
            median: 0.5,
            std: 0.5,
            start: datetime.datetime(2021, 1, 1, 0, 0),
            end: datetime.datetime(2021, 1, 2, 0, 0),
        }
        """
        summary_dict = summary.to_dict()
        stats_dict = {k: summary_dict[k] for k in ("statistics", "start", "end")}
        stats_dict.update(stats_dict.pop("statistics"))
        return stats_dict

    @staticmethod
    def _get_bins_dict_from_summary(
        summary: Union[MLOpsMinimalSummary, SeriesSummary], prefix: str
    ) -> Dict[str, Any]:
        """A helper function to extract bins-related data from a summary object.

        :param summary: The summary object to extract bins from.
        :param prefix: The prefix to use for the bins to specify the source.

        :return Dict[str, Any]: A dictionary containing bins-related data.

        Example:

        {
            "edges": [236238.671875, 308049.625],
            "labels": ["left_outlier", "q_20"],
            "values": [0.000, 0.204],
        }
        """
        return {
            f"{prefix}_edges": summary.bins.edges,
            f"{prefix}_labels": summary.bins.labels,
            f"{prefix}_values": summary.aggregated_values,
        }


class PreviewResultList(List[PreviewResult]):
    """This class implements the IAssayAnalysisList interface that offers
    a number of methods for analyzing and visualizing a list of assay results
    from an interactive run.

    Attributes:
        - parent_assay: The AssayV2 object that this result belongs to.
    """

    def __init__(self, arr: List[PreviewResult], parent_assay: AssayV2Builder) -> None:
        """Initializes the PreviewResultList object."""
        super().__init__(arr)
        self.parent_assay = parent_assay

    def _get_run_frequency_timedelta(self) -> pd.Timedelta:
        """Convert the assay's run frequency to a pandas Timedelta for use as padding.

        :return pd.Timedelta: The run frequency as a pandas Timedelta.
        """
        run_freq = self.parent_assay.scheduling.run_frequency

        # Handle RunFrequencyType1 (simple_run_frequency)
        if hasattr(run_freq, "simple_run_frequency"):
            simple_freq = run_freq.simple_run_frequency
            quantity = simple_freq.quantity
            unit = simple_freq.unit.value

            if unit == IntervalUnit.MINUTE:
                return pd.Timedelta(minutes=quantity)
            elif unit == IntervalUnit.HOUR:
                return pd.Timedelta(hours=quantity)
            elif unit == IntervalUnit.DAY:
                return pd.Timedelta(days=quantity)
            elif unit == IntervalUnit.WEEK:
                return pd.Timedelta(weeks=quantity)

        # If simple_run_frequency is not set, use legacy behaviour of using window width.
        if self.parent_assay.window is None:
            # Default to 1 hour if window is None
            return pd.Timedelta(hours=1)

        window_seconds = self.parent_assay.window.width.seconds

        if window_seconds <= 60:  # <= 1 minute
            return pd.Timedelta(minutes=1)
        elif window_seconds <= 3600:  # <= 1 hour
            return pd.Timedelta(hours=1)
        elif window_seconds <= 86400:  # <= 1 day
            return pd.Timedelta(days=1)
        else:  # > 1 day
            return pd.Timedelta(weeks=1)

    def _color(self, edge=False) -> List[str]:
        def _color_row(row: PreviewResult) -> str:
            field = self.parent_assay._get_iopath()
            val = cast(ScoreData, row.scores.additional_properties[field]).score
            thresh = self.parent_assay.targeting.iopath[0].thresholds
            if thresh is None or isinstance(thresh, Unset):
                return "green" if isinstance(val, float) else "red"
            warning = thresh.warning
            alert = thresh.alert

            # If val errored out, always return red. Most important.
            if not isinstance(val, float):
                return "red" if edge else "white"
            # If no thresholds are configured, always return green.
            elif warning is None and alert is None:
                return "green"
            # If an alert is configured and we're above it, red.
            elif isinstance(alert, float) and val >= alert:
                return "red"
            # If a warning is configured and we're above it, orange.
            elif isinstance(warning, float) and val >= warning:
                return "orange"
            # We are not in error and not above a threshold, but they are configured.
            else:
                return "green"

        return [_color_row(x) for x in self]

    def _chart_df(
        self,
        df: Union[pd.DataFrame, pd.Series],
        title: str,
        nth_x_tick: Optional[int] = None,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ) -> None:
        """Create a chart from a dataframe representation of an PreviewResultList.

        :param df: The dataframe representation of a list of preview results.
        :param title: The title of the chart.
        :param nth_x_tick: Controls the density of x ticks.
            Every nth x tick will be used for the chart.
        :param start: The start time of the chart. Both start and end have
            to be provided to be used.
        :param end: The end time of the chart. Both start and end have
            to be provided to be used.
        """
        if nth_x_tick is None:
            if len(df) > 10:
                nth_x_tick = len(df) // 10
        else:
            nth_x_tick = 6

        float_only_df = df["score"].map(lambda x: x if isinstance(x, float) else 0.0)

        fig, ax = plt.subplots()
        ax.scatter(
            df.start,
            float_only_df,
            color=self._color(),
            edgecolor=self._color(edge=True),
            plotnonfinite=True,
        )

        # add some padding to the x-axis
        padding = self._get_run_frequency_timedelta()
        xlim_start = df.start.min() - padding
        xlim_end = df.start.max() + padding

        ax.set_xlim(xlim_start, xlim_end)

        # generate ticks
        tick_times = pd.date_range(xlim_start, xlim_end, freq=padding)
        if nth_x_tick is not None and len(tick_times) > nth_x_tick:
            tick_times = pd.date_range(xlim_start, xlim_end, periods=nth_x_tick)

        ax.set_xticks(tick_times)
        ax.set_xticklabels(
            [t.strftime("%Y-%m-%d %H:%M:%S") for t in tick_times],
            rotation=30,
            ha="right",
        )

        plt.title(title)

        if start is not None and end is not None:
            plt.xlim(start, end)

        xfmt = mdates.DateFormatter(tz=df.start.dt.tz, fmt="%Y-%m-%d %H:%M:%S")
        ax.xaxis.set_major_formatter(xfmt)
        plt.grid()
        plt.show()

    def chart_iopaths(
        self,
        labels: Optional[List[str]] = None,
        selected_labels: Optional[List[str]] = None,
        nth_x_tick: Optional[int] = None,
    ) -> None:
        """Create a basic chart of the scores for each unique iopath of a PreviewResultList.

        :param labels: Custom labels for each unique iopath. If provided,
            these labels will be used in chart titles instead of raw iopath values.
        :param selected_labels: Labels to filter which iopaths to chart.
            If provided, only iopaths with labels in this list will be charted.
        :param nth_x_tick: Controls the density of x ticks.
            Every nth x tick will be used for the chart.
        """
        df = self.to_dataframe()
        if df.shape == (0, 0):
            raise ValueError("No io paths in this PreviewResultList.")

        for i, iopath in enumerate(df["iopath"].unique()):
            if selected_labels is None or (
                labels is not None and labels[i] in selected_labels
            ):
                df_ = df[df["iopath"] == iopath]
                if labels:
                    label = f"Assays V2 Score on '{labels[i]}' ({iopath}) vs Baseline"
                else:
                    label = f"Assays V2 Score on '{iopath}' vs Baseline"

                self._chart_df(df_, label, nth_x_tick=nth_x_tick)

    def chart_scores(
        self,
        title: Optional[str] = None,
        nth_x_tick: Optional[int] = 4,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ) -> None:
        """Create a chart of the scores from a dataframe representation of a PreviewResultList.

        :param title: The title of the chart.
        :param nth_x_tick: Controls the density of x ticks.
            Every nth x tick will be used for the chart.
        :param start: The start time of the chart. Both start and end have
            to be provided to be used.
        :param end: The end time of the chart. Both start and end have
            to be provided to be used.
        """
        if len(self) == 0:
            raise ValueError("No data in this PreviewResultList.")

        if title is None:
            title = "Assays V2 Score"

        df = self.to_dataframe()
        if df.shape == (0, 0):
            raise ValueError("No data in this PreviewResultList.")

        self._chart_df(df, title, nth_x_tick=nth_x_tick, start=start, end=end)

    def to_dataframe(self) -> pd.DataFrame:
        """Convert a PreviewResultList to a dataframe.

        :return pd.DataFrame: A dataframe representation of the list of preview results.
        """
        return pd.DataFrame(
            [
                {
                    "id": preview_result.raw.id,
                    "assay_id": preview_result.raw.assay_id,
                    "assay_name": self.parent_assay.name,
                    "iopath": self.parent_assay._get_iopath(),
                    "pipeline_id": preview_result.raw.pipeline_id,
                    "pipeline_name": self.parent_assay.pipeline_name,
                    "workspace_id": preview_result.raw.workspace_id,
                    "workspace_name": preview_result.raw.workspace_name,
                    "score": preview_result.scores.additional_properties[
                        preview_result._iopath
                    ].score,  # type: ignore[union-attr]
                    "start": preview_result.summaries[preview_result._iopath].start,
                    "min": preview_result.summaries[
                        preview_result._iopath
                    ].statistics.min_,
                    "max": preview_result.summaries[
                        preview_result._iopath
                    ].statistics.max_,
                    "mean": preview_result.summaries[
                        preview_result._iopath
                    ].statistics.mean,
                    "median": preview_result.summaries[
                        preview_result._iopath
                    ].statistics.median,
                    "std": preview_result.summaries[
                        preview_result._iopath
                    ].statistics.std,
                    "warning_threshold": self.parent_assay.targeting.iopath[
                        0
                    ].thresholds.warning,  # type: ignore[union-attr]
                    "alert_threshold": self.parent_assay.targeting.iopath[
                        0
                    ].thresholds.alert,  # type: ignore[union-attr]
                    "status": preview_result._calculate_status(
                        preview_result.scores.additional_properties[  # type: ignore[union-attr]
                            preview_result._iopath
                        ].score,
                        self.parent_assay.targeting.iopath[0].thresholds.warning,  # type: ignore[union-attr, arg-type]
                        self.parent_assay.targeting.iopath[0].thresholds.alert,  # type: ignore[union-attr, arg-type]
                    ),
                }
                for preview_result in self
            ]
        )

    def to_full_dataframe(self) -> pd.DataFrame:
        """Convert a PreviewResultList to a full dataframe.

        :return pd.DataFrame: A dataframe representation of the list of preview results.
        """
        return dict_list_to_dataframe([a.to_df_row() for a in self])
