"""This module features the Baseline class that configures baselines."""

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional, Tuple, Union, cast

import dateutil

from wallaroo.assay_config import (
    AssayConfig as V1AssayConfig,
    BinMode as V1BinMode,
    CalculatedBaseline as V1CalculatedBaseline,
    FixedBaseline as V1FixedBaseline,
    StaticBaseline as V1StaticBaseline,
    SummarizerConfig,
    UnivariateContinousSummarizerConfig as V1Summarizer,
    WindowConfig,
)
from wallaroo.assays_v2.summarizer import Summarizer
from wallaroo.assays_v2.targeting import Targeting
from wallaroo.utils import _unwrap
from wallaroo.wallaroo_ml_ops_api_client.api.assays.preview_baseline_binning import (
    PreviewBaselineBinningBody,
    sync_detailed as sync_detailed_preview_baseline_binning,
)
from wallaroo.wallaroo_ml_ops_api_client.models import (
    BaselineType0 as MLOpsSummaryBaseline,
    BaselineType1 as MLOpsStaticBaseline,
    BaselineType3 as MLOpsVectorBaseline,
)
from wallaroo.wallaroo_ml_ops_api_client.models.aggregation import Aggregation
from wallaroo.wallaroo_ml_ops_api_client.models.bin_mode_type_0 import BinModeType0
from wallaroo.wallaroo_ml_ops_api_client.models.bin_mode_type_1 import BinModeType1
from wallaroo.wallaroo_ml_ops_api_client.models.bin_mode_type_2 import BinModeType2
from wallaroo.wallaroo_ml_ops_api_client.models.bin_mode_type_4 import BinModeType4
from wallaroo.wallaroo_ml_ops_api_client.models.bins import Bins
from wallaroo.wallaroo_ml_ops_api_client.models.field_tagged_summaries import (
    FieldTaggedSummaries,
)
from wallaroo.wallaroo_ml_ops_api_client.models.series_summary import SeriesSummary
from wallaroo.wallaroo_ml_ops_api_client.models.series_summary_statistics import (
    SeriesSummaryStatistics,
)

if TYPE_CHECKING:
    # Imports that happen below in methods to fix circular import dependency
    # issues need to also be specified here to satisfy mypy type checking.
    from wallaroo.client import Client


class StaticBaseline(MLOpsStaticBaseline):
    """A Baseline from the server will always come in the form of a set of Summaries."""

    def summarize(self):
        # TODO: Expose summarize function like v1 to convert between baseline types.
        pass

    def _get_baseline_end(self) -> datetime:
        return self.static[-1]  # type: ignore[return-value]

    def _get_display_row(self) -> str:
        return """
        <tr><td>Baseline</td><td>TODO</td></tr>
        """


class SummaryBaseline(MLOpsSummaryBaseline):
    """This class represents a summary baseline.
    A Baseline from the MLOps API will always come in the form of a set of Summaries.
    """

    def _get_display_row(self) -> str:
        # TODO: Check dates
        return f"""
        <tr><td>Monitoring</td><td>{list(self.summary.to_dict().keys())}</td></tr>
        """

    def _get_baseline_end(self) -> datetime:
        return self.summary[list(self.summary.to_dict())[0]].end  # type: ignore[return-value]

    @staticmethod
    def _get_series_summary_statistics(
        baseline: V1StaticBaseline,
    ) -> SeriesSummaryStatistics:
        return SeriesSummaryStatistics(
            count=cast(int, baseline.static.get("count")),
            max_=cast(float, baseline.static.get("max")),
            mean=cast(float, baseline.static.get("mean")),
            median=cast(float, baseline.static.get("median")),
            min_=cast(float, baseline.static.get("min")),
            std=cast(float, baseline.static.get("std")),
        )

    @staticmethod
    def _get_v2_bin_mode(
        v1_mode: V1BinMode, v1_bin_count: int, v1_edges: List[float]
    ) -> Union[BinModeType0, BinModeType1, BinModeType2, BinModeType4]:
        if v1_mode == V1BinMode.NONE:
            return BinModeType0.NONE
        if v1_mode == V1BinMode.EQUAL:
            return BinModeType1(v1_bin_count)
        if v1_mode == V1BinMode.QUANTILE:
            return BinModeType2(v1_bin_count)
        # Provided
        return BinModeType4(v1_edges)

    @classmethod
    def _from_v1_config(cls, v1_config: V1AssayConfig) -> "SummaryBaseline":
        config_baseline = v1_config.baseline

        if isinstance(config_baseline, (V1CalculatedBaseline, V1FixedBaseline)):
            start = cast(str, config_baseline.calculated["fixed_window"].get("start"))
            baseline_start_at = dateutil.parser.parse(start)
            end = cast(str, config_baseline.calculated["fixed_window"].get("end"))
            baseline_end_at = dateutil.parser.parse(end)

            return StaticBaseline([baseline_start_at, baseline_end_at]).summarize()

        if isinstance(config_baseline, V1StaticBaseline):
            # At this point the assays v2 baseline calculation has already happened
            # using `AssayBuilder.build()` and `FixedWindowBaselineBuilder.build()`
            # and the result is converted to a V1StaticBaseline.
            config_summarizer = cast(V1Summarizer, v1_config.summarizer)
            parsed_path = _unwrap(v1_config.window.path).split()
            prefix = "in" if parsed_path[0] == "input" else "out"
            iopath = (
                f"{prefix}.{parsed_path[1]}"
                if len(parsed_path) == 2  # if the inference result is a scalar
                else f"{prefix}.{parsed_path[1]}.{parsed_path[2]}"
            )

            start = cast(str, config_baseline.static.get("start"))
            baseline_start_at = (
                dateutil.parser.parse(start) if start is not None else None
            )

            end = cast(str, config_baseline.static.get("end"))
            baseline_end_at = dateutil.parser.parse(end) if end is not None else end

            config_baseline.static["start"] = start
            config_baseline.static["end"] = end

            return cls.from_v1_summary(config_baseline, config_summarizer, iopath)

        raise Exception(
            f"Could not parse unknown V1 baseline type `{config_baseline.__class__.__name__}`.",
        )

    @classmethod
    def from_v1_summary(
        cls, baseline: V1StaticBaseline, summarizer: V1Summarizer, iopath: str
    ) -> "SummaryBaseline":
        """Create a SummaryBaseline from a V1Summarizer.
        A v1 summary is guaranteed to only contain one observed path.

        :param baseline: The v1 baseline.
        :param summarizer: The v1 summarizer.
        :param iopath: The iopath.

        :return: The SummaryBaseline object.
        """
        aggregation = Aggregation(baseline.static["aggregation"].value)  # type: ignore # mypy can't handle complex dicts
        # TODO: Move baseline calculation to assays v2, this is relying on v1.
        v1_edges = cast(List[Union[float, str]], baseline.static.get("edges"))
        # TODO: Handle infinity, make sure edge cases are clean.
        if v1_edges[-1] is None:
            # We could convert None instead of a str to INF if this is weird.
            v1_edges[-1] = "INFINITY"
        v1_labels = cast(List[str], baseline.static.get("edge_names"))
        v1_mode = summarizer.bin_mode
        v1_bin_count = summarizer.num_bins

        # OpenAPI doesn't know that "INFINITY" is allowed. This is manually deserialized into a float::INF by serde
        # In practice we never construct these manually, but we're converting v1 Baselines into the v2 Baseline, which is
        # not really a public interface.
        v1_edges_hack = cast(List[float], list(v1_edges))

        # TODO: Handle add_explicit_edges
        v2_mode = cast(
            Union[BinModeType0, BinModeType1, BinModeType2, BinModeType4],
            BinModeType0.NONE,
        )
        v2_mode = cls._get_v2_bin_mode(v1_mode, v1_bin_count, v1_edges_hack)

        v2_bins = Bins(edges=v1_edges_hack, labels=v1_labels, mode=v2_mode)

        series_summary = SeriesSummary(
            aggregated_values=cast(
                List[float], baseline.static.get("aggregated_values")
            ),
            aggregation=aggregation,
            bins=v2_bins,
            name=iopath,
            statistics=cls._get_series_summary_statistics(baseline),
            start=cast(Union[None, datetime], baseline.static.get("start", None)),
            end=cast(Union[None, datetime], baseline.static.get("end", None)),
        )
        summary = FieldTaggedSummaries.from_dict({iopath: series_summary.to_dict()})

        return SummaryBaseline(
            summary=summary
        )  # this is faking return from `/v2/api/assays/preview_baseline_binning`


def summarize_baseline_v2_from_v1_config(
    v1_config: V1AssayConfig, baseline_data: Optional[List[float]] = None
) -> Tuple[FieldTaggedSummaries, str]:
    """This function is used to summarize a baseline from a v1 config.
    It returns a SeriesSummary and the iopath of the baseline.
    Baseline summarization is called by `AssayBuilder.interactive_run()` (i.e. assays v1)
    after the `AssayConfig` object is already built.

    :param v1_config: The v1 config.
    :param baseline_data: The baseline data.

    :return: The SeriesSummary and the iopath of the baseline.
    """
    start, end = (
        v1_config.baseline.static["start"],  # type: ignore[attr-defined]
        v1_config.baseline.static["end"]  # type: ignore[attr-defined]
        if isinstance(v1_config.baseline, V1StaticBaseline)
        else None,
    )

    return summarize_baseline_v2_from_v1_args(
        client=v1_config.client,
        window=v1_config.window,
        summarizer=v1_config.summarizer,
        start=start,  # type: ignore[arg-type]
        end=end,  # type: ignore[arg-type]
        baseline_data=baseline_data,
        alert_threshold=cast(float, v1_config.alert_threshold),
        warning_threshold=cast(float, v1_config.warning_threshold),
        pipeline_id=cast(str, v1_config.pipeline_id),
        pipeline_name=cast(str, v1_config.pipeline_name),
        workspace_id=cast(str, v1_config.workspace_id),
        workspace_name=cast(str, v1_config.workspace_name),
    )


def summarize_baseline_v2_from_v1_args(
    client: "Client",
    window: WindowConfig,
    summarizer: SummarizerConfig,
    start: Optional[datetime],
    end: Optional[datetime],
    baseline_data: Optional[List[float]],
    alert_threshold: float,
    warning_threshold: float,
    pipeline_id: str,
    pipeline_name: str,
    workspace_id: str,
    workspace_name: str,
) -> Tuple[FieldTaggedSummaries, str]:
    """This function is used to summarize a baseline from a v1 config.
    It returns a SeriesSummary and the iopath of the baseline.
    Baseline summarization is called by `AssayBuilder.build()` (i.e. assays v1)
    before building the `AssayConfig` object.

    :param client: The client.
    :param window: The window.
    :param summarizer: The summarizer.
    :param start: The start.
    :param end: The end.
    :param alert_threshold: The alert threshold.
    :param warning_threshold: The warning threshold.
    :param pipeline_id: The pipeline id.
    :param pipeline_name: The pipeline name.
    :param workspace_id: The workspace id.
    :param workspace_name: The workspace name.

    :return: The SeriesSummary and the iopath of the baseline.
    """
    targeting = Targeting.from_v1_args(
        window=window,
        alert_threshold=alert_threshold,
        warning_threshold=warning_threshold,
        pipeline_id=pipeline_id,
        pipeline_name=pipeline_name,
        workspace_id=workspace_id,
        workspace_name=workspace_name,
    )
    iopath = targeting._get_iopath()
    baseline = (
        MLOpsVectorBaseline(vector=baseline_data)
        if baseline_data is not None
        else MLOpsStaticBaseline(static=[start, end])  # type: ignore[list-item]
    )

    body = PreviewBaselineBinningBody(
        baseline=baseline,  # type: ignore[arg-type]
        summarizer=Summarizer.from_v1_summarizer(cast(V1Summarizer, summarizer)),
        targeting=targeting,
    )
    response = sync_detailed_preview_baseline_binning(client=client.mlops(), body=body)

    if response.parsed is None:
        raise Exception("An error occurred while summarizing baseline: ", response)

    baseline_summary = cast(FieldTaggedSummaries, response.parsed)

    return baseline_summary, iopath
