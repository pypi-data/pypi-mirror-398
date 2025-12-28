from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union, cast

import gql  # type: ignore
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from ._inference_decode import dict_list_to_dataframe
from .object import (
    Object,
    RequiredAttributeMissing,
    rehydrate,
    value_if_present,
)
from .wallaroo_ml_ops_api_client.api.assay import (
    assays_get_assay_by_id,
    assays_set_active,
)
from .wallaroo_ml_ops_api_client.models import (
    AssaysGetAssayByIdBody,
    AssaysGetAssayByIdResponse200,
)
from .wallaroo_ml_ops_api_client.models.assays_set_active_body import (
    AssaysSetActiveBody,
)

if TYPE_CHECKING:
    from .client import Client


class Assay(Object):
    """An Assay represents a record in the database. An assay contains
    some high level attributes such as name, status, active, etc. as well
    as the sub objects Baseline, Window and Summarizer which specify how
    the Baseline is derived, how the Windows should be created and how the
    analysis should be conducted."""

    def __init__(self, client: "Client", data: Dict[str, Any]) -> None:
        self.client = client
        assert client is not None
        super().__init__(gql_client=client._gql_client, data=data)

    def _fill(self, data: Dict[str, Any]) -> None:
        for required_attribute in ["id"]:
            if required_attribute not in data:
                raise RequiredAttributeMissing(
                    self.__class__.__name__, required_attribute
                )
        self._id = int(data["id"])
        self._active = value_if_present(data, "active")
        self._status = value_if_present(data, "status")
        self._name = value_if_present(data, "name")
        self._warning_threshold = value_if_present(data, "warning_threshold")
        self._alert_threshold = value_if_present(data, "alert_threshold")
        self._pipeline_id = value_if_present(data, "pipeline_id")
        self._pipeline_name = value_if_present(data, "pipeline_name")
        self._workspace_id = value_if_present(data, "workspace_id")
        self._workspace_name = value_if_present(data, "workspace_name")

    def _fetch_attributes(self) -> Dict[str, Any]:
        assert self.client is not None
        ret = assays_get_assay_by_id.sync(
            client=self.client.mlops(),
            body=AssaysGetAssayByIdBody.from_dict({"id": self._id}),
        )
        if ret is None or not isinstance(ret, AssaysGetAssayByIdResponse200):
            raise Exception("Failed to fetch Assay by id")
        return ret.to_dict()

    def id(self) -> int:
        return self._id

    @rehydrate("_active")
    def active(self) -> bool:
        return cast(bool, self._active)

    @rehydrate("_status")
    def status(self) -> str:
        return cast(str, self._status)

    @rehydrate("_name")
    def name(self) -> str:
        return cast(str, self._name)

    @rehydrate("_warning_threshold")
    def warning_threshold(self) -> float:
        return cast(float, self._warning_threshold)

    @rehydrate("_alert_threshold")
    def alert_threshold(self) -> float:
        return cast(float, self._alert_threshold)

    @rehydrate("_pipeline_id")
    def pipeline_id(self) -> int:
        return cast(int, self._pipeline_id)

    @rehydrate("_pipeline_name")
    def pipeline_name(self) -> str:
        return cast(str, self._pipeline_name)

    @rehydrate("_workspace_id")
    def workspace_id(self) -> int:
        return cast(int, self._workspace_id)

    @rehydrate("_workspace_name")
    def workspace_name(self) -> str:
        return cast(str, self._workspace_name)

    @staticmethod
    def _extract_baseline_dates(baseline: Dict[str, Any]) -> str:
        if (
            baseline.get("static") is not None
            and baseline["static"].get("start") is not None
            and baseline["static"].get("end") is not None
        ):
            return f"Start:{baseline['static'].get('start')}, End:{baseline['static'].get('end')}"

        return "Uploaded File"

    @staticmethod
    def get_assay_info(
        client: "Client",
        assay_id: int,
        workspace_id: Optional[int] = None,
        workspace_name: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Get the assay information for the given assay_id
        :param client: Client object
        :param assay_id: int Assay Identifier
        :param workspace_id: Optiona[int] Workspace Identifier
        :param workspace_name: Optional[str] Workspace Name
        :return: pd.DataFrame
        """
        get_assay_info_request_dict = {
            "id": assay_id,
            "workspace_id": workspace_id,
            "workspace_name": workspace_name,
        }
        ret = assays_get_assay_by_id.sync(
            client=client.mlops(),
            body=AssaysGetAssayByIdBody.from_dict(get_assay_info_request_dict),
        )
        if ret is None:
            return Exception("Assay not found")

        if not isinstance(ret, AssaysGetAssayByIdResponse200):
            return Exception(ret.msg)

        raw_assay = ret.to_dict()
        summarizer = raw_assay["summarizer"]
        window = raw_assay["window"]
        assay_info_df = pd.DataFrame(
            [raw_assay],
            columns=[
                "id",
                "name",
                "active",
                "status",
                "pipeline_name",
                "last_run",
                "next_run",
                "alert_threshold",
                "workspace_id",
                "workspace_name",
            ],
        )
        assay_info_df["baseline"] = Assay._extract_baseline_dates(raw_assay["baseline"])
        assay_info_df["iopath"] = window["path"] if window else None
        assay_info_df["metric"] = summarizer["metric"]
        assay_info_df["num_bins"] = summarizer["num_bins"]
        assay_info_df["bin_weights"] = summarizer["bin_weights"]
        assay_info_df["bin_mode"] = summarizer["bin_mode"]
        return assay_info_df

    def turn_on(self):
        """Sets the Assay to active causing it to run and backfill any
        missing analysis."""

        ret = assays_set_active.sync(
            client=self.client.mlops(),
            body=AssaysSetActiveBody(self._id, True),
        )
        self._active = True
        return ret

    def turn_off(self):
        """Disables the Assay. No further analysis will be conducted until the assay
        is enabled."""
        ret = assays_set_active.sync(
            client=self.client.mlops(),
            body=AssaysSetActiveBody(self._id, False),
        )
        self._active = False
        return ret

    def set_alert_threshold(self, threshold: float):
        """Sets the alert threshold at the specified level. The status in the AssayAnalysis
        will show if this level is exceeded however currently alerting/notifications are
        not implemented."""
        res = self._gql_client.execute(
            gql.gql(
                """
            mutation SetActive($id: bigint!, $alert_threshold: Float!) {
                update_assay_by_pk(pk_columns: {id: $id}, _set: {alert_threshold: $alert_threshold}) {
                    id
                    active
                }
            }
            """
            ),
            variable_values={"id": self._id, "alert_threshold": threshold},
        )["update_assay_by_pk"]
        self._alert_threshold = threshold
        return res

    def set_warning_threshold(self, threshold: float):
        """Sets the warning threshold at the specified level. The status in the AssayAnalysis
        will show if this level is exceeded however currently alerting/notifications are
        not implemented."""

        res = self._gql_client.execute(
            gql.gql(
                """
            mutation SetActive($id: bigint!, $warning_threshold: Float!) {
                update_assay_by_pk(pk_columns: {id: $id}, _set: {warning_threshold: $warning_threshold}) {
                    id
                    active
                }
            }
            """
            ),
            variable_values={"id": self._id, "warning_threshold": threshold},
        )["update_assay_by_pk"]
        self._warning_threshold = threshold
        return res


def meta_df(assay_result: Dict, index_name) -> pd.DataFrame:
    """Creates a dataframe for the meta data in the baseline or window excluding the
    edge information.
    :param assay_result: The dict of the raw asset result"""
    return pd.DataFrame(
        {
            k: [assay_result[k]]
            for k in assay_result.keys()
            if k not in ["edges", "edge_names", "aggregated_values", "aggregation"]
        },
        index=[index_name],
    )


def edge_df(window_or_baseline: Dict) -> pd.DataFrame:
    """Creates a dataframe specifically for the edge information in the baseline or window.
    :param window_or_baseline: The dict from the assay result of either the window or baseline
    """

    data = {
        k: window_or_baseline[k]
        for k in ["edges", "edge_names", "aggregated_values", "aggregation"]
    }
    return pd.DataFrame(data)


class AssayAnalysis:
    """The AssayAnalysis class helps handle the assay analysis logs from the Plateau
    logs.  These logs are a json document with meta information on the assay and analysis
    as well as summary information on the baseline and window and information on the comparison
    between them."""

    def __init__(
        self,
        raw: Dict[str, Any],
        client: "Client",
        assay_name: Optional[str] = None,
    ):
        self.id = 0
        self.assay_id = 0
        self.assay_name = assay_name
        self.pipeline_id = 0
        self.pipeline_name = ""
        self.workspace_id = 0
        self.workspace_name = ""
        self.raw = raw
        self.iopath = ""
        self.score = 0.0
        self.status = ""
        self.alert_threshold = None
        self.warning_threshold = None
        self.window_summary: Dict[str, Any] = {}
        self.is_baseline_run = False
        for k, v in raw.items():
            setattr(self, k, v)
        # If an Assay is not uploaded yet, there wouldn't be an assay_id,
        # so there is no way of fetching these unless it's passed in to the constructor from assay_config.
        if raw["assay_id"] is not None:
            assert client is not None
            assay = Assay(client=client, data={"id": raw["assay_id"]})
            self.assay_name = assay.name()
            self.pipeline_id = assay.pipeline_id()
            self.pipeline_name = assay.pipeline_name()
            self.iopath = assay.get_assay_info(client=client, assay_id=raw["assay_id"])[
                "iopath"
            ][0]

    def baseline_stats(self) -> pd.DataFrame:
        """Creates a simple dataframe with the basic stats data for a baseline."""
        r = self.raw
        baseline = r["baseline_summary"]
        bs_df = meta_df(baseline, "Baseline")
        return bs_df.T

    def baseline_bins(self) -> pd.DataFrame:
        """Creates a simple dataframe to with the edge/bin data for a baseline."""
        r = self.raw

        baseline = r["baseline_summary"]
        bs_df = edge_df(baseline)
        bs_df.columns = [f"b_{c}" for c in bs_df.columns]  # type: ignore
        return bs_df.fillna(np.inf)

    def chart(self, show_scores: bool = True) -> None:
        """Create a chart showing the bins, values and scores of an assay result.
        `show_scores` will also label each bin with its final weighted (if specified) score.

        :param show_scores: Whether to show the scores for each bin.
        """
        # TODO: Fix for assays v2
        r = self.raw
        baseline = r["baseline_summary"]
        window = r["window_summary"]

        summarizer = r["summarizer"]
        es = summarizer["bin_mode"]
        vk = baseline["aggregation"]
        metric = summarizer["metric"]
        num_bins = summarizer["num_bins"]
        weighted = True if summarizer["bin_weights"] is not None else False
        score = r["score"]
        scores = r["scores"]
        index = r["bin_index"]

        print(f"baseline mean = {baseline['mean']}")
        if not self.is_baseline_run:
            print(f"window mean = {window['mean']}")
        print(f"baseline median = {baseline['median']}")
        if not self.is_baseline_run:
            print(f"window median = {window['median']}")
        print(f"bin_mode = {es}")
        print(f"aggregation = {vk}")
        print(f"metric = {metric}")
        print(f"weighted = {weighted}")
        if not self.is_baseline_run:
            print(f"score = {score}")
            print(f"scores = {scores}")
            print(f"index = {index}")

        title = f"{num_bins} {es} {vk} {metric}={score:5.3f} bin#={index} Weighted={weighted} {window['start']}"

        if (
            len(baseline["aggregated_values"])
            == len(window["aggregated_values"])
            == len(baseline["edge_names"])
        ):
            if vk == "Edges":
                _, ax = plt.subplots()
                for n, v in enumerate(baseline["aggregated_values"]):
                    plt.axvline(x=v, color="blue", alpha=0.5)
                    plt.text(v, 0, f"e{n}", color="blue")
                for n, v in enumerate(window["aggregated_values"]):
                    plt.axvline(x=v, color="orange", alpha=0.5)
                    plt.text(v, 0.1, f"e{n}", color="orange")
            else:
                _, ax = plt.subplots()

                last = "Min"
                bin_begin = "["
                bin_end = ")"
                edge_names = []
                for idx, (n, e) in enumerate(
                    zip(baseline["edge_names"], baseline["edges"])
                ):
                    if e not in (
                        None,
                        "INFINITY",
                    ):  # right most edge is returned as `INFINITY` from assays v2
                        next = f"{e:.1E}"
                        name = f"{n}\n{bin_begin}{last}, {next}{bin_end}"
                        last = next
                    else:
                        name = f"{n}\n({last}, Max]"
                    edge_names.append(name)
                    if idx >= 1:
                        bin_begin = "("
                    bin_end = "]"

                bar1 = plt.bar(
                    edge_names,
                    baseline["aggregated_values"],
                    alpha=0.50,
                    label=f"Baseline ({baseline['count']})",
                )
                if not self.is_baseline_run:
                    _ = plt.bar(
                        edge_names,
                        window["aggregated_values"],
                        alpha=0.50,
                        label=f"Window ({window['count']})",
                    )
                if len(edge_names) > 7:
                    ax.set_xticklabels(labels=edge_names, rotation=45)

                if show_scores and not self.is_baseline_run:
                    for i, bar in enumerate(bar1.patches):
                        ax.annotate(
                            f"{scores[i]:.4f}",
                            (bar.get_x() + bar.get_width() / 2, bar.get_height()),
                            ha="center",
                            va="center",
                            size=9,
                            xytext=(0, 8),
                            textcoords="offset points",
                        )
                plt.legend()
            ax.set_title(title)
            plt.xticks(rotation=45)
            plt.show()
        else:
            print(title)
            print(
                len(baseline["aggregated_values"]),
                len(window["aggregated_values"]),
                len(baseline["edge_names"]),
                len(window["edge_names"]),
            )
            print(baseline["aggregated_values"])
            print(window["aggregated_values"])
            print(baseline["edge_names"])
            print(window["edge_names"])
            return

    def compare_basic_stats(self) -> pd.DataFrame:
        """Creates a simple dataframe making it easy to compare a baseline and window."""
        r = self.raw
        baseline = r["baseline_summary"]
        window = r["window_summary"]

        bs_df = meta_df(baseline, "Baseline")
        ws_df = meta_df(window, "Window")
        df = pd.concat([bs_df, ws_df])

        text_cols = ["start", "end"]
        tdf = df[text_cols]
        df = df.drop(text_cols, axis=1)

        df.loc["diff"] = df.loc["Window"] - df.loc["Baseline"]
        df.loc["pct_diff"] = df.loc["diff"] / df.loc["Baseline"] * 100.0
        return pd.concat([df.T, tdf.T])

    def compare_bins(self) -> pd.DataFrame:
        """Creates a simple dataframe to compare the bin/edge information of baseline and window."""
        r = self.raw
        baseline = r["baseline_summary"]
        window = r["window_summary"]
        bs_df = edge_df(baseline)
        bs_df.columns = [f"b_{c}" for c in bs_df.columns]  # type: ignore
        if self.is_baseline_run:
            df = bs_df
        else:
            ws_df = edge_df(window)
            ws_df.columns = [f"w_{c}" for c in ws_df.columns]  # type: ignore
            df = pd.concat([bs_df, ws_df], axis=1)
            df["diff_in_pcts"] = df["w_aggregated_values"] - df["b_aggregated_values"]
        return df


class AssayAnalysisList:
    """Helper class primarily to easily create a dataframe from a list
    of AssayAnalysis objects."""

    def __init__(self, raw: List[AssayAnalysis]):
        self.raw = raw

    def __getitem__(self, index):
        return self.raw[index]

    def __len__(self):
        return len(self.raw)

    def _chart_df(
        self,
        df: Union[pd.DataFrame, pd.Series],
        title: str,
        nth_x_tick: Optional[int] = None,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ) -> None:
        """Given a dataframe representation of a list of assay results it creates a chart.

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

        plt.scatter(df.start, df.score, color=self.__pick_colors(df.status))
        plt.title(title)

        if start is not None and end is not None:
            plt.xlim(start, end)

        old_ticks = plt.xticks()[0]
        new_ticks = [t for i, t in enumerate(old_ticks) if i % nth_x_tick == 0]
        plt.xticks(ticks=new_ticks, rotation=90)

        plt.grid()
        plt.show()

    def chart_iopaths(
        self,
        labels: Optional[List[str]] = None,
        selected_labels: Optional[List[str]] = None,
        nth_x_tick: Optional[int] = None,
    ) -> None:
        """Creates a basic charts of the scores for each unique iopath of a list of assay results.

        :param labels: Custom labels for each unique iopath. If provided,
            these labels will be used in chart titles instead of raw iopath values.
        :param selected_labels: Labels to filter which iopaths to chart.
            If provided, only iopaths with labels in this list will be charted.
        :param nth_x_tick: Controls the density of x ticks.
            Every nth x tick will be used for the chart.
        """

        df = self.to_dataframe()
        if df.shape == (0, 0):
            raise ValueError("No io paths in this AssayAnalysisList.")

        for i, iopath in enumerate(df["iopath"].unique()):
            if selected_labels is None or (
                labels is not None and labels[i] in selected_labels
            ):
                df_ = df[df["iopath"] == iopath]
                if labels:
                    label = (
                        f"Model Insights Score on '{labels[i]}' ({iopath}) vs Baseline"
                    )
                else:
                    label = f"Model Insights Score on '{iopath}' vs Baseline"

                self._chart_df(df_, label, nth_x_tick=nth_x_tick)

    def chart_scores(
        self,
        title: Optional[str] = None,
        nth_x_tick: Optional[int] = 4,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ) -> None:
        """Creates a chart of the scores from dataframe representation of a list of assay results.

        :param title: The title of the chart.
        :param nth_x_tick: Controls the density of x ticks.
            Every nth x tick will be used for the chart.
        :param start: The start time of the chart. Both start and end have
            to be provided to be used.
        :param end: The end time of the chart. Both start and end have
            to be provided to be used.
        """
        if title is None:
            title = "Model Insights Score"

        df = self.to_dataframe()
        if df.shape == (0, 0):
            raise ValueError("No data in this AssayAnalysisList.")

        self._chart_df(df, title, nth_x_tick=nth_x_tick, start=start, end=end)

    def to_dataframe(self) -> pd.DataFrame:
        """Creates and returns a summary dataframe from the assay results."""
        return pd.DataFrame(
            [
                {
                    "id": a.id,
                    "assay_id": a.assay_id,
                    "assay_name": a.assay_name,
                    "iopath": a.iopath,
                    "pipeline_id": a.pipeline_id,
                    "pipeline_name": a.pipeline_name,
                    "workspace_id": a.workspace_id,
                    "workspace_name": a.workspace_name,
                    "score": a.score,
                    "start": a.window_summary["start"],
                    "min": a.window_summary["min"],
                    "max": a.window_summary["max"],
                    "mean": a.window_summary["mean"],
                    "median": a.window_summary["median"],
                    "std": a.window_summary["std"],
                    "warning_threshold": a.warning_threshold,
                    "alert_threshold": a.alert_threshold,
                    "status": a.status,
                }
                for a in self.raw
            ]
        )

    def to_full_dataframe(self) -> pd.DataFrame:
        """Creates and returns a dataframe with all values including inputs
        and outputs from the assay results."""
        return dict_list_to_dataframe([a.raw for a in self.raw])

    def __status_color(self, status: str):
        if status == "Ok":
            return "green"
        elif status == "Warning":
            return "orange"
        else:
            return "red"

    def __pick_colors(self, s):
        return [self.__status_color(status) for status in s]


class Assays(List[Assay]):
    """Wraps a list of assays for display in an HTML display-aware environment like Jupyter."""

    def _repr_html_(self) -> str:
        def row(assay) -> str:
            return (
                "<tr>"
                + f"<td>{assay.id()}</td>"
                + f"<td>{assay.name()}</td>"
                + f"<td>{assay.active()}</td>"
                + f"<td>{assay.status()}</td>"
                + f"<td>{assay.warning_threshold()}</td>"
                + f"<td>{assay.alert_threshold()}</td>"
                + f"<td>{assay.pipeline_id()}</td>"
                + f"<td>{assay.pipeline_name()}</td>"
                + f"<td>{assay.workspace_id()}</td>"
                + f"<td>{assay.workspace_name()}</td>"
                + "</tr>"
            )

        fields = [
            "Assay ID",
            "Assay Name",
            "Active",
            "Status",
            "Warning Threshold",
            "Alert Threshold",
            "Pipeline ID",
            "Pipeline Name",
            "Workspace ID",
            "Workspace Name",
        ]

        if self == []:
            return "(No Assays)"
        else:
            return (
                "<table>"
                + "<tr><th>"
                + "</th><th>".join(fields)
                + "</th></tr>"
                + ("".join([row(assay) for assay in self]))
                + "</table>"
            )
