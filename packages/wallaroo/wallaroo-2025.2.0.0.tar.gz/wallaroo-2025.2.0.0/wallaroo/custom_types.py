from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional, Protocol, runtime_checkable

if TYPE_CHECKING:
    import pandas as pd


@runtime_checkable
class IAssayAnalysis(Protocol):
    def chart(self, show_scores: bool = True) -> None:
        """Create a chart showing the bins, values and scores of an assay result.
        `show_scores` will also label each bin with its final weighted (if specified) score.

        :param show_scores: Whether to show the scores for each bin.
        """

    def compare_basic_stats(self) -> pd.DataFrame:
        """Compare basic stats between baseline and window.

        :return pd.DataFrame: A dataframe including stats, start and end times
            for the window against the baseline.
        """

    def compare_bins(self) -> pd.DataFrame:
        """Compare bins between baseline and window.

        :return pd.DataFrame: A dataframe including edges, labels and values
            for the window against the baseline.
        """


@runtime_checkable
class IAssayAnalysisList(Protocol):
    def _chart_df(
        self,
        df: pd.DataFrame,
        title: str,
        nth_x_tick: Optional[int] = None,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ) -> None:
        """Create a chart from a dataframe representation of an AssayAnalysisList.

        :param df: The dataframe representation of an AssayAnalysisList.
        :param title: The title of the chart.
        :param nth_x_tick: Controls the density of x ticks.
            Every nth x tick will be used for the chart.
        :param start: The start time of the chart. Both start and end have
            to be provided to be used.
        :param end: The end time of the chart. Both start and end have
            to be provided to be used.
        """

    def chart_iopaths(
        self,
        labels: Optional[List[str]] = None,
        selected_labels: Optional[List[str]] = None,
        nth_x_tick: Optional[int] = None,
    ) -> None:
        """Create a basic chart of the scores for each unique iopath of an AssayAnalysisList.

        :param labels: Custom labels for each unique iopath. If provided,
            these labels will be used in chart titles instead of raw iopath values.
        :param selected_labels: Labels to filter which iopaths to chart.
            If provided, only iopaths with labels in this list will be charted.
        :param nth_x_tick: Controls the density of x ticks.
            Every nth x tick will be used for the chart.
        """

    def chart_scores(
        self,
        title: Optional[str] = None,
        nth_x_tick: Optional[int] = 4,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ) -> None:
        """Create a chart of the scores from a dataframe representation of an AssayAnalysisList.

        :param title: The title of the chart.
        :param nth_x_tick: Controls the density of x ticks.
            Every nth x tick will be used for the chart.
        :param start: The start time of the chart. Both start and end have
            to be provided to be used.
        :param end: The end time of the chart. Both start and end have
            to be provided to be used.
        """

    def to_dataframe(self) -> pd.DataFrame:
        """Convert an AssayAnalysisList to a dataframe."""

    def to_full_dataframe(self) -> pd.DataFrame:
        """Convert an AssayAnalysisList to a full dataframe."""
