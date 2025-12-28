"""This module features classes related to an assay v2 result that help with analysis and visualization
for uploaded assays."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union, cast

import dateutil
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import pandas as pd

from wallaroo._inference_decode import dict_list_to_dataframe
from wallaroo.assay import AssayAnalysis, AssayAnalysisList
from wallaroo.assays_v2.baseline import SummaryBaseline
from wallaroo.wallaroo_ml_ops_api_client.models.aggregation import Aggregation
from wallaroo.wallaroo_ml_ops_api_client.models.assay_result_v2 import (
    AssayResultV2 as MLOPsAssayResultV2,
)
from wallaroo.wallaroo_ml_ops_api_client.models.bin_mode_type_0 import BinModeType0
from wallaroo.wallaroo_ml_ops_api_client.models.bin_mode_type_1 import BinModeType1
from wallaroo.wallaroo_ml_ops_api_client.models.bin_mode_type_2 import BinModeType2
from wallaroo.wallaroo_ml_ops_api_client.models.bin_mode_type_3 import BinModeType3
from wallaroo.wallaroo_ml_ops_api_client.models.bin_mode_type_4 import BinModeType4
from wallaroo.wallaroo_ml_ops_api_client.models.field_tagged_summaries import (
    FieldTaggedSummaries,
)
from wallaroo.wallaroo_ml_ops_api_client.models.score_data import ScoreData
from wallaroo.wallaroo_ml_ops_api_client.models.scores import Scores
from wallaroo.wallaroo_ml_ops_api_client.models.series_summary import SeriesSummary
from wallaroo.wallaroo_ml_ops_api_client.types import Unset
from wallaroo.workspace import Workspace

if TYPE_CHECKING:
    from .assay_v2 import AssayV2


class AssayResultV2(MLOPsAssayResultV2):
    """This class implements the IAssayAnalysis interface that offers
    a number of methods for analyzing and visualizing assay results.

    Attributes:
        - parent_assay: The AssayV2 object that this result belongs to.
        - raw: The raw AssayResultV2 object from the Wallaroo ML Ops API client.
    """

    def __init__(
        self, parent_assay: AssayV2, mlops_assay_result: MLOPsAssayResultV2
    ) -> None:
        """Initializes the AssayResultV2 object."""
        super().__init__(**mlops_assay_result.to_dict())
        self.parent_assay = parent_assay
        self.raw = mlops_assay_result
        self._baseline_summary: SeriesSummary = cast(
            SummaryBaseline, self.parent_assay.baseline
        ).summary[self.v1_iopath]
        self._window_summary: SeriesSummary = cast(
            FieldTaggedSummaries, self.raw.summaries
        )[self.v1_iopath]

    @property
    def v1_iopath(self) -> str:
        """Convert the v2 iopath to a v1 iopath."""
        return self.parent_assay.targeting._get_iopath()

    def chart(self, show_scores: bool = True) -> None:
        """Create a chart showing the bins, values and scores of an assay result.
        `show_scores` will also label each bin with its final weighted (if specified) score.

        :param show_scores: Whether to show the scores for each bin.
        """
        scores = cast(Scores, self.raw.scores)
        score_data = cast(ScoreData, scores[self.v1_iopath])
        bin_mode = self._window_summary.bins.mode
        weighted = isinstance(
            self.parent_assay.summarizer.univariate_continuous.bin_weights, List
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

        agg = self._window_summary.aggregation.value
        baseline_aggregated_values = self._baseline_summary.aggregated_values
        baseline_sample_size = self._baseline_summary.statistics.count
        window_aggregated_values = self._window_summary.aggregated_values
        window_sample_size = self._window_summary.statistics.count
        end = self.raw.window_end
        metric = self.parent_assay.summarizer.univariate_continuous.metric.value
        edge_names = self._window_summary.bins.labels

        title = f"{num_bins} {bin_mode_str} {agg} {metric}={score_data.score:5.3f} Weighted={weighted} {end}"

        _, ax = plt.subplots()

        if self._window_summary.aggregation == Aggregation.EDGES:
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
        window_values = self._window_summary.aggregated_values
        window_edges = self._window_summary.bins.edges
        window_labels = self._window_summary.bins.labels
        baseline_values = self._baseline_summary.aggregated_values
        baseline_edges = self._baseline_summary.bins.edges
        baseline_labels = self._baseline_summary.bins.labels

        window = pd.DataFrame(
            {
                "window_edges": window_edges,
                "window_labels": window_labels,
                "window_values": window_values,
            }
        )
        baseline = pd.DataFrame(
            {
                "baseline_edges": baseline_edges,
                "baseline_labels": baseline_labels,
                "baseline_values": baseline_values,
            }
        )
        df = pd.concat([baseline, window], axis=1)
        df["diff_in_pcts"] = df["window_values"] - df["baseline_values"]

        return df

    def to_df_row(self) -> Dict[str, Any]:
        """Convert the preview result to a dataframe row.

        :return Dict[str, Any]: A dataframe row.
        """
        alert = self.parent_assay.targeting.iopath[0].thresholds.alert  # type: ignore[union-attr]
        warning = self.parent_assay.targeting.iopath[0].thresholds.warning  # type: ignore[union-attr]
        score_data = cast(ScoreData, self.raw.scores[self.v1_iopath])  # type: ignore[index]
        bin_index = (
            score_data.bin_index
            if not isinstance(score_data.bin_index, Unset)
            else None
        )

        return {
            "id": self.raw.id,
            "assay_id": self.raw.assay_id,
            "window_start": self.raw.window_start,
            "analyzed_at": self.raw.analyzed_at,
            "elapsed_millis": self.raw.elapsed_millis,
            "pipeline_id": self.raw.pipeline_id,
            "workspace_id": self.raw.workspace_id,
            "workspace_name": self.raw.workspace_name,
            "baseline_summary": self._baseline_summary.to_dict(),
            "window_summary": self._window_summary.to_dict(),
            "warning_threshold": warning,
            "alert_threshold": alert,
            "bin_index": bin_index,
            "summarizer": self.parent_assay.summarizer.to_dict(),
            "status": self._calculate_status(
                score_data.score,
                warning,  # type: ignore[arg-type]
                alert,  # type: ignore[arg-type]
            ),
            "created_at": self.raw.created_at,
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

    def _into_v1(self):
        d = {}

        summary = self.raw.summaries.to_dict().get(self.v1_iopath, {})
        # v2 assays don't have ids.
        # d.id = self.raw.id
        d["assay_id"] = self.raw.assay_id
        d["assay_name"] = self.parent_assay.name
        # TODO: Pipeline name to ID
        # d.pipeline_id =
        d["pipeline_name"] = self.parent_assay.targeting.data_origin.pipeline_name
        workspace_id = self.parent_assay.targeting.data_origin.workspace_id
        d["workspace_id"] = workspace_id
        d["workspace_name"] = Workspace(
            self.parent_assay._client, {"id": workspace_id}
        ).name()

        d["raw"] = self.raw
        d["iopath"] = self.v1_iopath
        d["score"] = self.raw.scores[self.v1_iopath].score
        d["status"] = self.raw.status.value
        d["alert_threshold"] = (
            self.parent_assay.targeting.iopath[0].thresholds.alert
            if self.parent_assay.targeting.iopath[0].thresholds
            else None
        )
        d["warning_threshold"] = (
            self.parent_assay.targeting.iopath[0].thresholds.warning
            if self.parent_assay.targeting.iopath[0].thresholds
            else None
        )
        d["window_summary"] = summary
        d["is_baseline_run"] = False
        return AssayAnalysis(d, self.parent_assay._client, d["assay_name"], True)

    @staticmethod
    def _get_stats_dict_from_summary(summary: SeriesSummary) -> Dict[str, Any]:
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


class AssayResultsList(List[AssayResultV2]):
    """This class implements the IAssayAnalysisList interface that offers
    a number of methods for analyzing and visualizing a list of assay results.

    Attributes:
        - parent_assay: The AssayV2 object that this result belongs to.
    """

    def __init__(self, arr: List[AssayResultV2], parent_assay: AssayV2):
        """Initializes the AssayResultsList object."""
        super().__init__(arr)
        self.parent_assay = parent_assay

    def _into_v1(self):
        return AssayAnalysisList([x._into_v1() for x in self])

    def _repr_html_(self):
        def row(result: AssayResultV2):
            # TODO: Pass in client for this
            # fmt = result.client._time_format
            fmt = "%Y-%d-%b %H:%M:%S"

            summary_html = ""
            if result.raw.summaries:
                summaries = result.raw.summaries.to_dict()
                for key in summaries:
                    summary_html += f"""<details>
                  <summary>{key}</summary>
                  {summaries[key]}
                </details>"""

            score_html = ""
            if result.raw.scores:
                scores = result.raw.scores.to_dict()
                score_html = "<br/>".join(
                    [f"<div>{score}: {scores[score]}</div>" for score in scores]
                )
            workspace_id = result.raw.workspace_id
            workspace_name = Workspace(
                result.parent_assay._client, {"id": workspace_id}
            ).name()
            return (
                "<tr>"
                + f"<td>{result.raw.window_start.strftime(fmt)}</td>"
                + f"<td>{result.raw.window_end.strftime(fmt)}</td>"
                + f"<td>{workspace_id}</td>"
                + f"<td>{workspace_name}</td>"
                # + f"<td>{result.assay_id}</td>"
                + f"<td>{score_html}</td>"
                + f"<td>{result.raw.status}</td>"
                + f"<td>{summary_html}</td>"
                + f"<td>{result.raw.created_at.strftime(fmt)}</td>"
                + f"<td>{result.raw.updated_at.strftime(fmt)}</td>"
                + "</tr>"
            )

        fields = [
            "window_start",
            "window_end",
            "workspace_id",
            "workspace_name",
            # "assay_id",
            "scores",
            "status",
            "summaries",
            "created_at",
            "updated_at",
        ]

        if not self:
            return "(no results)"
        else:
            return (
                "<table>"
                + "<tr><th>"
                + "</th><th>".join(fields)
                + "</th></tr>"
                + ("".join([row(p) for p in self]))
                + "</table>"
            )

    def _color(self, edge=False):
        def _color_row(row: AssayResultV2):
            field = row.parent_assay._get_iopath()
            scores = row.raw.scores
            if scores is None or isinstance(scores, Unset) or field not in scores:  # type: ignore
                return "grey"
            val = cast(ScoreData, scores.additional_properties[field]).score
            thresh = row.parent_assay.targeting.iopath[0].thresholds
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
        """Create a chart from a dataframe representation of an AssayResultsList.

        :param df: The dataframe representation of a list of assay results.
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
                nth_x_tick = 1

        float_only_df = df["score"].map(lambda x: x if isinstance(x, float) else 0.0)
        start_times = df.start.map(lambda x: dateutil.parser.parse(x))

        plt.scatter(
            start_times,
            float_only_df,
            color=self._color(),
            edgecolor=self._color(edge=True),
            plotnonfinite=True,
        )
        plt.title(title)

        if start is not None and end is not None:
            plt.xlim(start, end)

        old_ticks = plt.xticks()[0]
        new_ticks = [t for i, t in enumerate(old_ticks) if i % nth_x_tick == 0]

        ax = plt.gca()
        ax.xaxis.set_major_locator(mticker.FixedLocator(new_ticks))
        formatter = mdates.DateFormatter("%H:%M:%S")
        ax.xaxis.set_major_formatter(formatter)

        for label in ax.get_xticklabels(which="major", minor=True):
            label.set(rotation=30, horizontalalignment="right")

        first_visible_date = mdates.num2date(new_ticks[0])
        date_label = first_visible_date.strftime("%Y-%b-%d")
        plt.gcf().text(0.95, 0.001, date_label, ha="right", fontsize=10)

        plt.tight_layout()
        plt.grid()
        plt.show()

    def chart_iopaths(
        self,
        labels: Optional[List[str]] = None,
        selected_labels: Optional[List[str]] = None,
        nth_x_tick: Optional[int] = None,
    ) -> None:
        """Create a basic chart of the scores for each unique iopath of an AssayResultsList.

        :param labels: Custom labels for each unique iopath. If provided,
            these labels will be used in chart titles instead of raw iopath values.
        :param selected_labels: Labels to filter which iopaths to chart.
            If provided, only iopaths with labels in this list will be charted.
        :param nth_x_tick: Controls the density of x ticks.
            Every nth x tick will be used for the chart.
        """
        df = self.to_dataframe()
        if df.shape == (0, 0):
            raise ValueError("No io paths in this AssayResultsList.")

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
        """Create a chart of the scores from a dataframe representation of an AssayResultsList.

        :param title: The title of the chart.
        :param nth_x_tick: Controls the density of x ticks.
            Every nth x tick will be used for the chart.
        :param start: The start time of the chart. Both start and end have
            to be provided to be used.
        :param end: The end time of the chart. Both start and end have
            to be provided to be used.
        """
        if len(self) == 0:
            raise ValueError("No data in this AssayResultsList.")

        if title is None:
            title = "Assays V2 Score"

        df = self.to_dataframe()
        if df.shape == (0, 0):
            raise ValueError("No data in this AssayResultsList.")

        self._chart_df(df, title, nth_x_tick=nth_x_tick, start=start, end=end)

    def to_dataframe(self) -> pd.DataFrame:
        """Convert an AssayResultsList to a dataframe.

        :return pd.DataFrame: A dataframe representation of the list of assay results.
        """
        return pd.DataFrame(
            [
                {
                    "id": assay_result.raw.id,
                    "assay_id": assay_result.raw.assay_id,
                    "assay_name": self.parent_assay.name,
                    "iopath": assay_result.v1_iopath,
                    "pipeline_id": assay_result.raw.pipeline_id,
                    "pipeline_name": self.parent_assay.targeting.data_origin.pipeline_name,
                    "workspace_id": assay_result.raw.workspace_id,
                    "workspace_name": assay_result.raw.workspace_name,
                    "score": assay_result.scores[assay_result.v1_iopath]["score"],  # type: ignore[index]
                    "start": assay_result.summaries[assay_result.v1_iopath]["start"],  # type: ignore[index]
                    "min": assay_result.summaries[assay_result.v1_iopath]["statistics"][  # type: ignore[index]
                        "min"
                    ],
                    "max": assay_result.summaries[assay_result.v1_iopath]["statistics"][  # type: ignore[index]
                        "max"
                    ],
                    "mean": assay_result.summaries[assay_result.v1_iopath][  # type: ignore[index]
                        "statistics"
                    ]["mean"],
                    "median": assay_result.summaries[assay_result.v1_iopath][  # type: ignore[index]
                        "statistics"
                    ]["median"],
                    "std": assay_result.summaries[assay_result.v1_iopath][  # type: ignore[index]
                        "statistics"
                    ]["std"],
                    "warning_threshold": self.parent_assay.targeting.iopath[
                        0
                    ].thresholds.warning,  # type: ignore[union-attr]
                    "alert_threshold": self.parent_assay.targeting.iopath[
                        0
                    ].thresholds.alert,  # type: ignore[union-attr]
                    "status": assay_result._calculate_status(
                        assay_result.scores[assay_result.v1_iopath]["score"],  # type: ignore[index, arg-type]
                        self.parent_assay.targeting.iopath[0].thresholds.warning,  # type: ignore[union-attr, arg-type]
                        self.parent_assay.targeting.iopath[0].thresholds.alert,  # type: ignore[union-attr, arg-type]
                    ),
                }
                for assay_result in self
            ]
        )

    def to_full_dataframe(self) -> pd.DataFrame:
        """Convert an AssayResultsList to a full dataframe.

        :return pd.DataFrame: A dataframe representation of the list of assay results.
        """
        return dict_list_to_dataframe([a.to_df_row() for a in self])
