import json
import math
from abc import ABC, abstractmethod
from collections import Counter
from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union, cast

import dateutil
import httpx
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pyarrow as pa  # type: ignore
import seaborn as sns

from wallaroo.assay import AssayAnalysis, AssayAnalysisList
from wallaroo.custom_types import IAssayAnalysis, IAssayAnalysisList
from wallaroo.exceptions import handle_errors
from wallaroo.utils import _ensure_tz, _unwrap, is_assays_v2_enabled
from wallaroo.wallaroo_ml_ops_api_client.client import AuthenticatedClient

from .wallaroo_ml_ops_api_client.api.assay import (
    assays_run_interactive,
    assays_summarize,
)
from .wallaroo_ml_ops_api_client.models.assays_run_interactive_body import (
    AssaysRunInteractiveBody,
)
from .wallaroo_ml_ops_api_client.models.assays_summarize_body import (
    AssaysSummarizeBody,
)
from .wallaroo_ml_ops_api_client.models.assays_summarize_response_200 import (
    AssaysSummarizeResponse200,
)

if TYPE_CHECKING:
    # Imports that happen below in methods to fix circular import dependency
    # issues need to also be specified here to satisfy mypy type checking.
    from wallaroo.client import Client


class BinMode(str, Enum):
    """How should we calculate the bins.
    NONE - no bins. Only useful if we only care about the mean, median, etc.
    EQUAL - evenly spaced bins: min - max / num_bins
    QUANTILE - based on percentages. If num_bins is 5 then quintiles
    so bins are created at the 20%, 40%, 60%, 80% and 100% points.
    PROVIDED - user provides the edge points for the bins.
    """

    NONE = "None"
    EQUAL = "Equal"
    QUANTILE = "Quantile"
    PROVIDED = "Provided"


class Aggregation(str, Enum):
    """What we use to calculate the score.
    EDGES - distnces between the edges.
    DENSITY - percentage of values that fall in each bin.
    CUMULATIVE - cumulative percentage that fall in the bins."""

    EDGES = "Edges"
    DENSITY = "Density"
    CUMULATIVE = "Cumulative"


class Metric(str, Enum):
    """How we calculate the score.
    MAXDIFF - maximum difference between corresponding bins.
    SUMDIFF - sum of differences between corresponding bins.
    PSI - Population Stability Index"""

    MAXDIFF = "MaxDiff"
    SUMDIFF = "SumDiff"
    PSI = "PSI"


class SummarizerConfig(object):
    """The summarizer specifies how the bins of the baseline and
    window should be compared."""

    def __init__(self):
        pass

    def to_json(self) -> str:
        return json.dumps(self, indent=4, default=ConfigEncoder)


class UnivariateContinousSummarizerConfig(SummarizerConfig):
    """The UnivariateContinousSummarizer analyizes one input or output feature
    (Univariate) at a time. Expects the values to be continous or at least numerous
    enough to fall in various/all the bins."""

    def __init__(
        self,
        bin_mode: BinMode,
        aggregation: Aggregation,
        metric: Metric,
        num_bins: int,
        bin_weights: Optional[List[float]] = None,
        bin_width: Optional[float] = None,
        provided_edges: Optional[List[float]] = None,
        add_outlier_edges: bool = True,
    ):
        self.type = "UnivariateContinuous"
        self.bin_mode = bin_mode
        self.aggregation = aggregation
        self.metric = metric
        self.num_bins = num_bins
        self.bin_weights = bin_weights
        self.bin_width = bin_width
        self.provided_edges = provided_edges
        self.add_outlier_edges = add_outlier_edges


class SummarizerBuilder(ABC):
    @abstractmethod
    def build(self) -> SummarizerConfig:
        pass


class UnivariateContinousSummarizerBuilder(SummarizerBuilder):
    """Builds the UnviariateSummarizer"""

    def __init__(self: "UnivariateContinousSummarizerBuilder"):
        self.bin_mode = BinMode.QUANTILE
        self.aggregation = Aggregation.DENSITY
        self.metric = Metric.PSI
        self.num_bins = 5
        self.bin_weights: Optional[List[float]] = None
        self.bin_width: Optional[float] = None
        self.provided_edges: Optional[List[float]] = None
        self.add_outlier_edges = True

    def build(self) -> UnivariateContinousSummarizerConfig:
        if self.bin_mode == BinMode.PROVIDED:
            if self.provided_edges is None:
                raise ValueError("Edges must be provided with BinMode.PROVIDED")
        else:
            if self.provided_edges is not None:
                raise ValueError(
                    f"Edges may not be provided with bin mode {self.bin_mode}"
                )

        sum = UnivariateContinousSummarizerConfig(
            self.bin_mode,
            self.aggregation,
            self.metric,
            self.num_bins,
            self.bin_weights,
            self.bin_width,
            self.provided_edges,
            self.add_outlier_edges,
        )
        return sum

    def add_bin_mode(self, bin_mode: BinMode, edges: Optional[List[float]] = None):
        """Sets the binning mode. If BinMode.PROVIDED is specified a list of edges
        is also required."""
        if bin_mode == BinMode.PROVIDED:
            if edges is None:
                raise ValueError("Edges must be provided with BinMode.PROVIDED")

        self.bin_mode = bin_mode
        self.add_bin_edges(edges)
        return self

    def add_num_bins(self, num_bins: int):
        """Sets the number of bins. If weights have been previously set they
        must be set to none to allow changing the number of bins."""

        if num_bins != self.num_bins and self.bin_weights is not None:
            if num_bins + 2 != len(self.bin_weights):
                msg = (
                    f"({len(self.bin_weights)}) have already been set. "
                    + "Please set them to None before changing the number of bins."
                )
                raise ValueError(msg)

        if num_bins != self.num_bins and self.provided_edges is not None:
            if not (
                len(self.provided_edges) == num_bins
                or len(self.provided_edges) == num_bins + 1
            ):
                msg = (
                    f"({len(self.provided_edges)}) bin edges have already been set. "
                    + "Please set them to None before changing the number of bins."
                )
                raise ValueError(msg)

        self.num_bins = num_bins
        return self

    def add_bin_weights(self, weights: Union[List[float], None]):
        """Specifies the weighting to be given to the bins. The number of weights
        must be 2 larger than the number of bins to accomodate outliers smaller
        and outliers larger than values seen in the baseline.
        The passed in values can be whole or real numbers and do not need to add
        up to 1 or any other specific value as they will be normalized during the
        score calculation phase.
        The weights passed in can be none to remove previously specified weights
        and to allow changing of the number of bins."""

        if weights is not None:
            if self.num_bins + 2 != len(weights):
                msg = (
                    f"The number of weights ({len(weights)}) "
                    + f"must be 2 more ({self.num_bins + 2}) than the "
                    + f"number of bins ({self.num_bins}) to allow for the "
                    + "left and right outlier bins."
                )
                raise ValueError(msg)
        self.bin_weights = weights
        return self

    def add_metric(self, metric: Metric):
        """Sets the metric mode."""
        self.metric = metric
        return self

    def add_aggregation(self, aggregation: Aggregation):
        """Sets the aggregation style."""
        self.aggregation = aggregation
        return self

    def add_bin_edges(self, edges: Union[List[float], None]):
        """Specifies the right hand side (max value) of the bins. The number
        of edges must be equal to or one more than the number of bins. When
        equal to the number of bins the edge for the left outlier bin is
        calculated from the baseline. When an additional edge (one more than
        number of bins) that first (lower) value is used as the max value for
        the left outlier bin.  The max value for the right hand outlier bin is
        always Float MAX.
        """

        if edges is not None:
            if not (len(edges) == self.num_bins or len(edges) == self.num_bins + 1):
                msg = (
                    f"The number of edges ({len(edges)}) "
                    + f"must be equal to ({self.num_bins}) or one more "
                    + f"({self.num_bins + 1 }) than the number of bins to account "
                    + "for the left outlier bin."
                )
                raise ValueError(msg)
            edges = sorted(edges)

        self.provided_edges = edges
        return self


class WindowConfig(object):
    """Configures a window to be compared against the baseline."""

    def __init__(
        self,
        pipeline_name: str,
        width: str,
        model_name: Optional[str] = None,
        start: Optional[datetime] = None,
        interval: Optional[str] = None,
        path: Optional[str] = None,
        workspace_id: Optional[int] = None,
        locations: List[str] = [],
    ):
        self.pipeline_name = pipeline_name
        self.model_name = model_name
        self.width = width
        self.start = start
        self.interval = interval
        self.path = path
        self.workspace_id = workspace_id
        self.locations = locations

    def to_json(self) -> str:
        return json.dumps(self, indent=4, default=ConfigEncoder)


class BaselineConfig(object):
    """Abstract base class for Baseline config objects. Currently
    only CalculatedBaseline (fixed window) and StaticBaseline are implemented."""

    def __init__(self):
        pass

    def to_json(self) -> str:
        return json.dumps(self, indent=4, default=ConfigEncoder)


# Baseline config as per the API spec could be of two types: CalculatedBaseline which takes the baseline config
#  to calculate the baseline summary on the fly, or it takes StaticBaseline which has the baseline summary calculated
#  by calling the "assays/summarize" endpoint.
#  Product decided to support only Static Baseline for now. So, CalculatedBaseline is not
#  used in sdk, but let's keep it just in case.
class CalculatedBaseline(BaselineConfig):
    """The CalculatedBaseline is calculated from the inferences from a
    specific time window."""

    def __init__(
        self,
        pipeline_name: str,
        model_name: str,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        locations: List[str] = [],
    ):
        self.calculated = {
            "fixed_window": {
                "pipeline": pipeline_name,
                "model": model_name,
                "start_at": start.isoformat() if start is not None else None,
                "end_at": end.isoformat() if end is not None else None,
                "locations": locations,
            }
        }


class FixedBaseline(CalculatedBaseline):
    """The FixedBaseline is calculated from the inferences from a
    specific time window."""

    def __init__(
        self,
        pipeline_name: str,
        model_name: str,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        locations: List[str] = [],
    ):
        self.calculated = {
            "fixed_window": {
                "pipeline": pipeline_name,
                "model": model_name,
                "start_at": start.isoformat() if start is not None else None,
                "end_at": end.isoformat() if end is not None else None,
                "locations": locations,
            }
        }


class StaticBaseline(BaselineConfig):
    """The StaticBaseline is pre-calculated data from the inferences in a
    specific time window."""

    def __init__(
        self,
        count: int,
        min_: float,
        max_: float,
        mean: float,
        median: float,
        std: float,
        edges: List[float],
        edge_names: List[str],
        aggregated_values: List[float],
        aggregation: Aggregation,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ):
        self.static = {
            "count": count,
            "min": min_,
            "max": max_,
            "mean": mean,
            "median": median,
            "std": std,
            "edges": edges,
            "edge_names": edge_names,
            "aggregated_values": aggregated_values,
            "aggregation": aggregation,
            "start": start.isoformat() if start is not None else None,
            "end": end.isoformat() if end is not None else None,
        }


class BaselineBuilder(ABC):
    @abstractmethod
    def build(self) -> BaselineConfig:
        pass

    def to_json(self) -> str:
        return json.dumps(self, indent=4, default=ConfigEncoder)


def _summarize_baseline_data(
    payload: Dict[str, Any], client: "Client"
) -> AssaysSummarizeResponse200:
    """Summarize the baseline data."""

    mlops_client = client.mlops()
    response = assays_summarize.sync(
        client=mlops_client,
        body=AssaysSummarizeBody.from_dict(payload),
    )
    if response is None:
        raise Exception("Failed to summarize baseline data")

    if not isinstance(response, AssaysSummarizeResponse200):
        raise Exception(response)

    return response


class VectorBaselineBuilder(BaselineBuilder):
    """Helps create a config object for a VectorBaseline."""

    def __init__(
        self,
        client: "Client",
        pipeline_name: str,
        alert_threshold: Optional[float],
        warning_threshold: Optional[float],
        pipeline_id: Optional[int],
        workspace_name: Optional[str],
    ):
        self.client = client
        self.baseline_data: Optional[List[float]] = None
        self.window: Optional[WindowConfig] = None
        self.summarizer: Optional[SummarizerConfig] = None
        self.pipeline_name = pipeline_name
        self.alert_threshold = alert_threshold
        self.warning_threshold = warning_threshold
        self.pipeline_id = pipeline_id
        self.workspace_name = workspace_name

    def add_baseline_data(self, baseline_data: np.ndarray) -> "VectorBaselineBuilder":
        """Add the baseline data."""
        # Replace NaN values with None needed to send a valid payload to the API
        self.baseline_data = np.where(  # type: ignore[call-overload]
            np.isnan(baseline_data), None, baseline_data
        ).tolist()
        return self

    def add_summarizer(self, summarizer: SummarizerConfig) -> "VectorBaselineBuilder":
        """Add the summarizer."""
        self.summarizer = summarizer
        return self

    def add_window(self, window: WindowConfig) -> "VectorBaselineBuilder":
        """Add the window."""
        self.window = window
        return self

    def add_workspace_id(self, workspace_id: int) -> "VectorBaselineBuilder":
        """Add the workspace id."""
        self.workspace_id = workspace_id
        return self

    def build(self) -> StaticBaseline:
        """Create the StaticBaseline object."""
        if is_assays_v2_enabled():
            from wallaroo.assays_v2.baseline import summarize_baseline_v2_from_v1_args

            series_summary, iopath = summarize_baseline_v2_from_v1_args(
                client=self.client,
                window=cast(WindowConfig, self.window),
                summarizer=cast(SummarizerConfig, self.summarizer),
                start=None,
                end=None,
                baseline_data=self.baseline_data,
                alert_threshold=cast(float, self.alert_threshold),
                warning_threshold=cast(float, self.warning_threshold),
                pipeline_id=cast(str, self.pipeline_id),
                pipeline_name=cast(str, self.pipeline_name),
                workspace_id=cast(str, self.workspace_id),
                workspace_name=cast(str, self.workspace_name),
            )
            baseline_summary = series_summary[iopath]

            return StaticBaseline(
                count=baseline_summary.statistics.count,
                min_=baseline_summary.statistics.min_,
                max_=baseline_summary.statistics.max_,
                mean=baseline_summary.statistics.mean,
                median=baseline_summary.statistics.median,
                std=baseline_summary.statistics.std,
                edges=baseline_summary.bins.edges,
                edge_names=baseline_summary.bins.labels,
                aggregated_values=baseline_summary.aggregated_values,
                aggregation=Aggregation(baseline_summary.aggregation),
                start=None,
                end=None,
            )
        else:
            vector = {"vector": self.baseline_data}
            payload = {
                "summarizer": self.summarizer.__dict__.copy(),
                "baseline": vector,
            }
            response = _summarize_baseline_data(payload, self.client)

            return StaticBaseline(
                count=response.count,
                min_=response.min_,
                max_=response.max_,
                mean=response.mean,
                median=response.median,
                std=response.std,
                edges=response.edges,
                edge_names=response.edge_names,
                aggregated_values=response.aggregated_values,
                aggregation=Aggregation(response.aggregation),
                start=cast(datetime, response.start),
                end=cast(datetime, response.end),
            )


class FixedWindowBaselineBuilder(BaselineBuilder):
    """Helps to easily create the config object for a FixedBaseline."""

    def __init__(
        self,
        client: "Client",
        pipeline_name: str,
        alert_threshold: Optional[float] = None,
        warning_threshold: Optional[float] = None,
        pipeline_id: Optional[int] = None,
        workspace_name: Optional[str] = None,
    ):
        self.client = client
        self.pipeline_name = pipeline_name
        self.model_name: Optional[str] = None
        self.start: Optional[datetime] = None
        self.end: Optional[datetime] = None
        self.iopath: Optional[str] = None
        self.workspace_id: Optional[int] = None
        self.summarizer: Optional[SummarizerConfig] = None
        self.locations: List[str] = []
        self.alert_threshold = alert_threshold
        self.warning_threshold = warning_threshold
        self.pipeline_id = pipeline_id
        self.workspace_name = workspace_name
        self.window: Optional[WindowConfig] = None

    def add_model_name(self, model_name: str) -> "FixedWindowBaselineBuilder":
        """Specify the model to use in the baseline"""
        self.model_name = model_name
        return self

    def add_start(self, start: datetime) -> "FixedWindowBaselineBuilder":
        """Specify the start of the window for the baseline"""
        self.start = start
        return self

    def add_end(self, end: datetime) -> "FixedWindowBaselineBuilder":
        """Specify the end of the window for the baseline"""
        self.end = end
        return self

    def add_iopath(self, iopath: str) -> "FixedWindowBaselineBuilder":
        """Specify the path to the inference data"""
        self.iopath = iopath
        return self

    def add_location_filter(self, locations: List[str]) -> "FixedWindowBaselineBuilder":
        self.locations = locations
        return self

    def add_workspace_id(self, workspace_id: int) -> "FixedWindowBaselineBuilder":
        """Specify the workspace id for the inference data"""
        self.workspace_id = workspace_id
        return self

    def add_summarizer(
        self, summarizer: SummarizerConfig
    ) -> "FixedWindowBaselineBuilder":
        """Specify the summarizer to use"""
        self.summarizer = summarizer
        return self

    def add_window(self, window: WindowConfig) -> "FixedWindowBaselineBuilder":
        """Specify the window to use"""
        self.window = window
        return self

    def build(self) -> StaticBaseline:
        """Create the FixedBaseline object."""
        start = _ensure_tz(_unwrap(self.start))
        end = _ensure_tz(_unwrap(self.end))
        # convert to ms
        width = f"{int((end - start).total_seconds() * 1000)} ms"

        if is_assays_v2_enabled():
            from wallaroo.assays_v2.baseline import summarize_baseline_v2_from_v1_args

            series_summary, iopath = summarize_baseline_v2_from_v1_args(
                client=self.client,
                window=cast(WindowConfig, self.window),
                summarizer=cast(SummarizerConfig, self.summarizer),
                start=start,
                end=end,
                baseline_data=None,
                alert_threshold=cast(float, self.alert_threshold),
                warning_threshold=cast(float, self.warning_threshold),
                pipeline_id=cast(str, self.pipeline_id),
                pipeline_name=cast(str, self.pipeline_name),
                workspace_id=cast(str, self.workspace_id),
                workspace_name=cast(str, self.workspace_name),
            )
            baseline_summary = series_summary[iopath]

            return StaticBaseline(
                count=baseline_summary.statistics.count,
                min_=baseline_summary.statistics.min_,
                max_=baseline_summary.statistics.max_,
                mean=baseline_summary.statistics.mean,
                median=baseline_summary.statistics.median,
                std=baseline_summary.statistics.std,
                edges=baseline_summary.bins.edges,
                edge_names=baseline_summary.bins.labels,
                aggregated_values=baseline_summary.aggregated_values,
                aggregation=Aggregation(baseline_summary.aggregation),
                start=cast(datetime, baseline_summary.start),
                end=cast(datetime, baseline_summary.end),
            )
        else:
            payload = {
                "summarizer": self.summarizer.__dict__.copy(),
                "baseline": {
                    "fixed_window": {
                        "pipeline_name": self.pipeline_name,
                        "model_name": self.model_name,
                        "start": start.isoformat(),
                        "width": width,
                        "path": self.iopath,
                        "workspace_id": self.workspace_id,
                        "locations": self.locations,
                    }
                },
            }
            response = _summarize_baseline_data(payload, self.client)

            return StaticBaseline(
                count=response.count,
                min_=response.min_,
                max_=response.max_,
                mean=response.mean,
                median=response.median,
                std=response.std,
                edges=response.edges,
                edge_names=response.edge_names,
                aggregated_values=response.aggregated_values,
                aggregation=Aggregation(response.aggregation),
                start=cast(datetime, response.start),
                end=cast(datetime, response.end),
            )


class WindowBuilder(object):
    """Helps build a WindowConfig. model and width are required but there are no
    good default values for them because they depend on the baseline. We leave it
    up to the assay builder to configure the window correctly after it is created.
    """

    def __init__(self, pipeline_name: str):
        self.pipeline_name = pipeline_name
        self.model_name: Optional[str] = None
        self.width: Optional[str] = "24 hours"
        self.start: Optional[datetime] = None
        self.interval: Optional[str] = None
        self.path: Optional[str] = None
        self.workspace_id: Optional[int] = None
        self.locations: List[str] = []

    def add_model_name(self, model_name: str):
        """The model name (model_id) that the window should analyze."""
        self.model_name = model_name
        return self

    def _duration_kw_to_str(self, **kwargs) -> str:
        interval_names = ["minute", "hour", "day", "week"]
        duration_str = None
        kw_count = 0

        for interval_name in interval_names:
            plural = interval_name + "s"

            for kw in [interval_name, plural]:
                if kw in kwargs:
                    duration_str = f"{kwargs[kw]} {plural}"
                    kw_count += 1

        if kw_count == 0:
            raise Exception(
                "Please specify one of 'minutes', 'hours', 'days' or 'weeks' keyword args"
            )

        elif kw_count > 1:
            raise Exception(
                "Please specify only one of 'minutes', 'hours', 'days' or 'weeks' keyword args"
            )
        else:
            return _unwrap(duration_str)

    def add_width(self, **kwargs: int):
        """The width of the window to use when collecting data for analysis."""
        self.width = self._duration_kw_to_str(**kwargs)
        return self

    def add_interval(self, **kwargs: int):
        """The width of the window to use when collecting data for analysis."""
        self.interval = self._duration_kw_to_str(**kwargs)
        return self

    def add_location_filter(self, locations: List[str] = []):
        self.locations = locations
        return self

    def add_start(self, start: datetime):
        self.start = start
        return self

    def add_path(self, path: str):
        self.path = path
        return self

    def add_workspace_id(self, workspace_id: int):
        self.workspace_id = workspace_id
        return self

    def build(self) -> WindowConfig:
        start = _ensure_tz(self.start) if self.start else None

        return WindowConfig(
            pipeline_name=self.pipeline_name,
            width=_unwrap(self.width),
            model_name=self.model_name,
            start=start,
            interval=self.interval,
            path=self.path,
            workspace_id=self.workspace_id,
            locations=self.locations,
        )


def ConfigEncoder(o):
    """Used to format datetimes as we need when encoding to JSON"""
    if isinstance(o, datetime):
        return o.isoformat()
    if isinstance(o, AuthenticatedClient):
        return None
    else:
        return o.__dict__


class AssayConfig(object):
    """Configuration for an Assay record."""

    def __init__(
        self,
        client: "Client",
        name: str,
        pipeline_id: int,
        pipeline_name: str,
        active: bool,
        status: str,
        baseline: BaselineConfig,
        window: WindowConfig,
        summarizer: SummarizerConfig,
        warning_threshold: Optional[float],
        alert_threshold: float,
        run_until: Optional[datetime],
        workspace_id: Optional[int],
        workspace_name: Optional[str],
    ):
        self.client = client
        self.name = name
        self.pipeline_id = pipeline_id
        self.pipeline_name = pipeline_name
        self.active = active
        self.status = status
        self.baseline = baseline
        self.window = window
        self.summarizer = summarizer
        self.warning_threshold = warning_threshold
        self.alert_threshold = alert_threshold
        self.run_until = run_until
        self.workspace_id = workspace_id
        self.workspace_name = workspace_name

    def to_json(self) -> str:
        payload = self.__dict__.copy()
        payload.pop("client", None)
        payload.pop("model_insights_url", None)
        return json.dumps(payload, indent=4, default=ConfigEncoder)

    def interactive_run(self) -> IAssayAnalysisList:
        """Runs this assay interactively. The assay is not saved to the database
        nor are analyis records saved to a Plateau topic. Useful for exploring
        pipeline inference data and experimenting with thresholds."""
        from wallaroo.assays_v2 import AssayV2Builder

        if is_assays_v2_enabled():
            if self.window.start:
                return AssayV2Builder._from_v1_config(self).preview(
                    self.window.start, self.run_until
                )
            elif isinstance(self.baseline, CalculatedBaseline) or isinstance(
                self.baseline, FixedBaseline
            ):
                return AssayV2Builder._from_v1_config(self).preview(
                    self.baseline.calculated["fixed_window"]["end_at"], self.run_until
                )
            elif isinstance(self.baseline, StaticBaseline):
                end: str = self.baseline.static["end"]  # type: ignore
                return AssayV2Builder._from_v1_config(self).preview(
                    dateutil.parser.parse(end), self.run_until
                )

        payload = {
            **json.loads(self.to_json()),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        assert self.client is not None
        mlops_client = self.client.mlops()
        mlops_client = mlops_client.with_timeout(httpx.Timeout(5 * 60, connect=5.0))
        ret = assays_run_interactive.sync(
            client=mlops_client,
            body=AssaysRunInteractiveBody.from_dict(payload),
        )

        analysis_list = []
        if ret is not None:
            if not isinstance(ret, List):
                raise Exception(ret.msg)

            analysis_list = [
                AssayAnalysis(
                    raw=ar.to_dict(), client=self.client, assay_name=self.name
                )
                for ar in ret
            ]

        return AssayAnalysisList(analysis_list)

    def interactive_baseline_run(self) -> Optional[IAssayAnalysis]:
        # This is a hack to get the baseline summary data into the shape,
        # that the previous assays/run_interactive_baseline endpoint returned.
        # We are "faking" the response from the old endpoint which is not available anymore
        # with results from the new summarize endpoint.

        assert isinstance(self.baseline, StaticBaseline)
        summary_data = {
            "count": self.baseline.static["count"],
            "min": self.baseline.static["min"],
            "max": self.baseline.static["max"],
            "mean": self.baseline.static["mean"],
            "median": self.baseline.static["median"],
            "std": self.baseline.static["std"],
            "edges": self.baseline.static["edges"],
            "edge_names": self.baseline.static["edge_names"],
            "aggregated_values": self.baseline.static["aggregated_values"],
            "aggregation": self.baseline.static["aggregation"],
            "start": self.baseline.static["start"],
            "end": self.baseline.static["end"],
        }

        raw_data = {
            "baseline_summary": summary_data,
            "window_summary": summary_data,
            "summarizer": self.summarizer.__dict__,
            "assay_id": None,
            "score": 0,
            "scores": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            "bin_index": None,
        }
        assay_analysis = AssayAnalysis(
            raw=raw_data, client=self.client, assay_name=self.name
        )
        assay_analysis.is_baseline_run = True
        return assay_analysis

    def interactive_input_run_arrow(
        self, inferences: pd.DataFrame, labels: Optional[List[str]]
    ) -> AssayAnalysisList:
        if len(inferences) == 0:
            return AssayAnalysisList([])

        all_assays = []
        sample_input = inferences.iloc[0]["in"]["tensor"]
        if labels and len(sample_input) != len(labels):
            print(
                f"Labels are not the same len {len(labels)} as inputs {len(sample_input)}"
            )

        print("column distinct_vals label           largest_pct")
        for idx0 in range(len(sample_input)):
            values = []
            for _, row in inferences.iterrows():
                values.append(row["in"]["tensor"][idx0])
            counter = Counter(values)
            value_pct = [c / len(values) for c in counter.values()]
            value_pct.sort()
            largest_pct = value_pct[-1]
            distinct_values = len(counter.keys())
            label = labels[idx0] if labels else ""
            # TODO: Rule of thumb may need better way to distinguish
            msg = (
                "*** May not be continuous feature"
                if distinct_values < 5 or largest_pct > 0.90
                else ""
            )
            print(f"{idx0:6} {distinct_values:13} {label:15} {largest_pct:0.4f} {msg}")

            self.window.path = f"input tensor {idx0}"

            assays = self.interactive_run()
            all_assays.extend(assays.raw)  # type: ignore[attr-defined]

        return AssayAnalysisList(all_assays)

    def interactive_input_run_legacy(
        self, inferences: List[Dict], labels: Optional[List[str]]
    ) -> AssayAnalysisList:
        all_assays = []
        inference = inferences[0]

        print("input column distinct_vals label           largest_pct")
        # TODO extend this to work for any input shape
        inputs = inference["original_data"]["tensor"]
        for idx0, _ in enumerate(inputs):
            if labels and len(inputs[idx0]) != len(labels):
                print(
                    f"Labels are not the same len {len(labels)} as inputs {len(inference['inputs'][idx0])}"
                )
            for idx1, _ in enumerate(inputs[idx0]):
                values = []
                for inf in inferences:
                    values.append(inf["original_data"]["tensor"][idx0][idx1])
                counter = Counter(values)
                value_pct = [c / len(values) for c in counter.values()]
                value_pct.sort()
                largest_pct = value_pct[-1]
                distinct_values = len(counter.keys())
                label = labels[idx1] if labels else ""
                # TODO: Rule of thumb may need better way to distinguish
                msg = (
                    "*** May not be continuous feature"
                    if distinct_values < 5 or largest_pct > 0.90
                    else ""
                )
                print(
                    f"{idx0:5} {idx1:5} {distinct_values:14} {label:15} {largest_pct:0.4f} {msg}"
                )

                self.window.path = f"inputs {idx0} {idx1}"

                assays = self.interactive_run()
                all_assays.extend(assays.raw)  # type: ignore[attr-defined]

        return AssayAnalysisList(all_assays)

    def interactive_input_run(
        self, inferences: Union[List[Dict], pd.DataFrame], labels: Optional[List[str]]
    ) -> AssayAnalysisList:
        """Analyzes the inputs given to create an interactive run for each feature
        column. The assay is not saved to the database nor are analyis records saved
        to a Plateau topic. Usefull for exploring inputs for possible causes when a
        difference is detected in the output."""

        if isinstance(inferences, pd.DataFrame):
            return self.interactive_input_run_arrow(inferences, labels)
        return self.interactive_input_run_legacy(inferences, labels)


class AssayBuilder(object):
    """Helps build an AssayConfig"""

    def __init__(
        self,
        client: "Client",
        name: str,
        pipeline_id: int,
        pipeline_name: str,
        iopath: str,
        model_name: Optional[str] = None,
        baseline_start: Optional[datetime] = None,
        baseline_end: Optional[datetime] = None,
        baseline_data: Optional[np.ndarray] = None,
    ):
        self.client = client
        assert self.client is not None
        self.name = name
        self.pipeline_id = pipeline_id
        self.pipeline_name: str = pipeline_name
        self.active = True
        self.status = "created"
        self.iopath = iopath
        self.baseline: Optional[BaselineConfig] = None
        self.baseline_builder: Optional[
            Union[FixedWindowBaselineBuilder, VectorBaselineBuilder]
        ] = None
        self.window: Optional[WindowConfig] = None
        self.summarizer: Optional[SummarizerConfig] = None
        self.warning_threshold: Optional[float] = None
        self.alert_threshold: float = 0.25
        self.run_until: Optional[datetime] = None
        self.workspace_id = self.client.get_current_workspace().id()
        self.workspace_name = self.client.get_current_workspace().name()

        self.window_builder_ = (
            WindowBuilder(self.pipeline_name)
            .add_path(self.iopath)
            .add_workspace_id(self.workspace_id)
        )
        if model_name is not None:
            self.window_builder_.add_model_name(model_name)

        self.summarizer_builder = UnivariateContinousSummarizerBuilder()

        self.baseline_data = baseline_data
        self._col_name: Optional[str] = None
        self._set_col_name()

        if self.baseline_data is None:
            self.baseline_builder = (
                FixedWindowBaselineBuilder(
                    client=self.client,
                    pipeline_name=self.pipeline_name,
                    alert_threshold=self.alert_threshold,
                    warning_threshold=self.warning_threshold,
                    pipeline_id=self.pipeline_id,
                    workspace_name=self.workspace_name,
                )
                .add_iopath(self.iopath)
                .add_workspace_id(self.workspace_id)
            )
            if baseline_start is not None:
                self.baseline_builder.add_start(baseline_start)
            if baseline_end is not None:
                self.baseline_builder.add_end(baseline_end)
            if model_name is not None:
                self.baseline_builder.add_model_name(model_name)
        else:
            self.baseline_builder = (
                VectorBaselineBuilder(
                    client=self.client,
                    pipeline_name=self.pipeline_name,
                    alert_threshold=self.alert_threshold,
                    warning_threshold=self.warning_threshold,
                    pipeline_id=self.pipeline_id,
                    workspace_name=self.workspace_name,
                )
                .add_baseline_data(self.baseline_data)
                .add_workspace_id(self.workspace_id)
            )

    def baseline_dataframe(self):
        if self.baseline_data is not None:
            baseline_df = pd.DataFrame({self._col_name: self.baseline_data})
        else:
            baseline_df = self.client.get_pipeline_inference_dataframe(
                self.client.get_topic_name(self.pipeline_id),
                _unwrap(self.baseline_builder.start),
                _unwrap(self.baseline_builder.end),
                self.baseline_builder.model_name,
            )
        return baseline_df

    def baseline_histogram(
        self, bins: Optional[Union[str, int]] = None, log_scale: bool = False
    ):
        df = self.baseline_dataframe()

        n_bins = calc_bins(df.shape[0], bins)
        # type inference for the bins param to histplot is incorrect: str vs str|int.
        sns.histplot(data=df, x=self._col_name, bins=n_bins, log_scale=log_scale).set(  # type: ignore
            title=f"Baseline '{self.iopath}'", xlabel=f"{self.iopath}"
        )
        plt.show()

    def baseline_kde(self, log_scale: bool = False):
        df = self.baseline_dataframe()
        sns.kdeplot(data=df, x=self._col_name, log_scale=log_scale).set(
            title=f"Baseline '{self.iopath}'", xlabel=f"{self.iopath}"
        )
        plt.grid()
        plt.show()

    def baseline_ecdf(self, log_scale: bool = False):
        df = self.baseline_dataframe()
        sns.ecdfplot(data=df, x=self._col_name, log_scale=log_scale).set(
            title=f"Baseline '{self.iopath}'", xlabel=f"{self.iopath}"
        )
        plt.grid()
        plt.show()

    @handle_errors()
    def _get_inference_start_date(
        self,
        client: "Client",
        pipeline_id: int,
    ) -> datetime:
        assert client
        topic = client.get_topic_name(pipeline_id)
        params = dict()
        params["page_size"] = 1
        params["order"] = "asc"  # type: ignore

        headers = {"Accept": "application/vnd.apache.arrow.file"}
        resp = client.httpx_client.post(
            f"/v1/logs/topic/{topic}/records",
            params=params,
            json={},
            headers=headers,
        )
        resp.raise_for_status()
        if resp is None:
            raise ValueError("Couldn't get inference start date.")
        with pa.ipc.open_file(resp.content) as reader:
            entries = reader.read_all()
            clean_entries = client._cleanup_arrow_data_for_display(entries)
        return clean_entries["time"][0].as_py()

    def _add_window_start_date_if_not_provided(self):
        if isinstance(self.baseline_builder, VectorBaselineBuilder):
            if self.window_builder_.start is None:
                window_start = self._get_inference_start_date(
                    self.client, self.pipeline_id
                )
                self.window_builder_.add_start(window_start)

    def build(self) -> AssayConfig:
        self.summarizer = self.summarizer_builder.build()
        baseline_builder = cast(
            Union[FixedWindowBaselineBuilder, VectorBaselineBuilder],
            self.baseline_builder,
        )
        baseline_builder.add_summarizer(self.summarizer)
        self._add_window_start_date_if_not_provided()
        self.window = self.window_builder_.build()
        if isinstance(
            baseline_builder,
            (FixedWindowBaselineBuilder, VectorBaselineBuilder),
        ):
            baseline_builder.add_window(cast(WindowConfig, self.window))
        self.baseline = baseline_builder.build()

        run_until = _ensure_tz(self.run_until) if self.run_until else None
        return AssayConfig(
            self.client,
            self.name,
            self.pipeline_id,
            self.pipeline_name,
            self.active,
            self.status,
            _unwrap(self.baseline),
            _unwrap(self.window),
            _unwrap(self.summarizer),
            self.warning_threshold,
            self.alert_threshold,
            run_until,
            self.workspace_id,
            self.workspace_name,
        )

    def upload(self) -> Union[int, str]:
        config = self.build()
        res = self.client.upload_assay(config)  # type: ignore
        return res

    def add_name(self, name: str):
        """Specify the assay name"""
        self.name = name
        return self

    def add_active(self, active: bool):
        """Specify if the assay is active or not"""
        self.active = active
        return self

    def add_iopath(self, iopath: str):
        """Specify what the assay should analyze. Should start with input or output and have
        indexes (zero based) into row and column: For example 'input 0 1' specifies the second
        column of the first input."""

        iopath = iopath.strip()
        assert iopath.lower().startswith("input") or iopath.lower().startswith("output")
        self.iopath = iopath
        self._set_col_name()
        return self

    def add_location_filter(self, locations: List[str]):
        self.locations = locations
        self.window_builder_.add_location_filter(locations)
        if isinstance(self.baseline_builder, FixedWindowBaselineBuilder):
            self.baseline_builder.add_location_filter(locations)
        return self

    def fixed_baseline_builder(self):
        """Specify creates a fixed baseline builder for this assay builder."""

        bb = FixedWindowBaselineBuilder(_unwrap(self.pipeline_name))
        self.baseline_builder = bb
        return bb

    def add_baseline(self, baseline: BaselineConfig):
        """Adds a specific baseline created elsewhere."""
        self.baseline = baseline
        self.baseline_data = None
        return self

    def window_builder(self):
        """Returns this assay builders window builder."""
        return self.window_builder_

    def add_window(self, window: WindowConfig):
        """Adds a window created elsewhere."""
        self.window = window
        return self

    def univariate_continuous_summarizer(self) -> UnivariateContinousSummarizerBuilder:
        """Creates and adds an UCS to this assay builder."""
        ucsb = UnivariateContinousSummarizerBuilder()
        self.summarizer_builder = ucsb
        return ucsb

    def add_summarizer(self, summarizer: SummarizerConfig):
        """Adds the summarizer created elsewhere to this builder."""
        self.summarizer = summarizer
        return self

    def add_warning_threshold(self, warning_threshold: float):
        """Specify the warning threshold for this assay."""
        self.warning_threshold = warning_threshold
        return self

    def add_alert_threshold(self, alert_threshold: float):
        """Specify the alert threshold for this assay."""
        self.alert_threshold = alert_threshold
        return self

    def add_run_until(self, run_until: datetime):
        """ "How long should this assay run. Primarily useful for
        interactive runs to limit the number of analysis."""
        self.run_until = run_until
        return self

    def _set_col_name(self) -> None:
        assert self.iopath is not None
        path_parts = self.iopath.split()
        self._col_name = "_".join(
            path_parts[:3]
            if len(path_parts) > 2
            else path_parts + ["0"]  # for scalars we don't specify indexes in assays v2
        )


def calc_bins(num_samples: int, bins: Optional[Union[str, int]]) -> Union[str, int]:
    """If the users specifies a number of bins or a strategy for calculating
    it use that. Else us the min of the square root or 50."""

    if bins is None:
        return min(int(math.sqrt(num_samples)), 50)
    else:
        return bins
