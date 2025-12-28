"""This module features the AssayV2Builder that helps with the creation of an AssayV2 object."""

from datetime import datetime, timedelta
from typing import TYPE_CHECKING, List, Optional, Union, cast

from wallaroo.assay_config import (
    Aggregation as V1Aggregation,
    AssayConfig as V1AssayConfig,
    Metric as V1Metric,
)
from wallaroo.assays_v2.baseline import StaticBaseline, SummaryBaseline
from wallaroo.assays_v2.preview_result import PreviewResult, PreviewResultList
from wallaroo.assays_v2.scheduling import Scheduling
from wallaroo.assays_v2.summarizer import Summarizer
from wallaroo.assays_v2.targeting import Targeting
from wallaroo.assays_v2.window import RollingWindow
from wallaroo.utils import _unwrap
from wallaroo.wallaroo_ml_ops_api_client.api.assays.preview import (
    PreviewBody,
    sync_detailed as sync_detailed_preview,
)
from wallaroo.wallaroo_ml_ops_api_client.api.assays.schedule import (
    ScheduleBody,
    sync_detailed as sync_detailed_schedule,
)
from wallaroo.wallaroo_ml_ops_api_client.models.aggregation import Aggregation
from wallaroo.wallaroo_ml_ops_api_client.models.bin_mode_type_0 import BinModeType0
from wallaroo.wallaroo_ml_ops_api_client.models.bin_mode_type_1 import BinModeType1
from wallaroo.wallaroo_ml_ops_api_client.models.bin_mode_type_2 import BinModeType2
from wallaroo.wallaroo_ml_ops_api_client.models.bin_mode_type_3 import BinModeType3
from wallaroo.wallaroo_ml_ops_api_client.models.bin_mode_type_4 import BinModeType4
from wallaroo.wallaroo_ml_ops_api_client.models.data_origin import DataOrigin
from wallaroo.wallaroo_ml_ops_api_client.models.data_path import DataPath
from wallaroo.wallaroo_ml_ops_api_client.models.interval_unit import IntervalUnit
from wallaroo.wallaroo_ml_ops_api_client.models.metric import Metric
from wallaroo.wallaroo_ml_ops_api_client.models.pg_interval import PGInterval
from wallaroo.wallaroo_ml_ops_api_client.models.run_frequency_type_1 import (
    RunFrequencyType1 as MLOpsSimpleRunFrequency,
)
from wallaroo.wallaroo_ml_ops_api_client.models.thresholds import Thresholds
from wallaroo.wallaroo_ml_ops_api_client.models.univariate_continuous import (
    UnivariateContinuous,
)
from wallaroo.wallaroo_ml_ops_api_client.models.window_width_duration import (
    WindowWidthDuration,
)
from wallaroo.wallaroo_ml_ops_api_client.types import Unset
from wallaroo.workspace import Workspace

if TYPE_CHECKING:
    # Imports that happen below in methods to fix circular import dependency
    # issues need to also be specified here to satisfy mypy type checking.
    from wallaroo.client import Client

    from .assay_v2 import AssayV2


class AssayV2Builder:
    """This class helps with the creation of an AssayV2 object.

    Attributes:
        - client: The Wallaroo Client object.
        - targeting: The Targeting object that specifies the data origin and io paths.
        - scheduling: The Scheduling object that specifies the scheduling of the assay.
        - summarizer: The Summarizer object that specifies the summarizer for the assay.
        - bin_mode: The bin mode of the assay.
        - window: The RollingWindow object that specifies the window width.
        - name: The name of the assay.
        - bin_weights: The bin weights of the assay.
    """

    def __init__(
        self, client: "Client", pipeline_id: int, pipeline_name: str, workspace_id: int
    ):
        self.client = client
        self.pipeline_id = pipeline_id
        self.pipeline_name = pipeline_name
        self.workspace_id = workspace_id
        self.workspace_name = Workspace(self.client, {"id": workspace_id}).name()

        # Set the defaults
        self.targeting: Targeting = Targeting(
            DataOrigin(
                pipeline_id, pipeline_name, self.workspace_id, self.workspace_name
            ),
            [],
        )
        self.baseline: Optional[Union[StaticBaseline, SummaryBaseline]] = None
        self.scheduling: Scheduling = Scheduling(
            datetime.now().astimezone(),
            MLOpsSimpleRunFrequency(PGInterval(1, IntervalUnit.DAY)),
        )
        self.summarizer: Optional[Summarizer] = None
        self.bin_mode: Optional[
            Union[BinModeType1, BinModeType2, BinModeType3, BinModeType4, BinModeType0]
        ] = None
        self.window: Optional[RollingWindow] = None
        self.name = f"{pipeline_name} assay"
        self.bin_weights: Union[List[float], None, Unset] = None

    def _validate(self):
        if self.baseline is None:
            raise Exception("No baseline is configured. See `set_baseline`")

        if len(self.targeting.iopath) <= 0:
            raise Exception("No monitoring paths are configured. See `add_monitoring`")

        if self.metric is None:
            raise Exception("No metric is configured.")

        if self.aggregation is None:
            raise Exception("No aggregation is configured")

        if self.bin_mode is None:
            raise Exception("No binning mode is configured")

    @classmethod
    def _from_v1_config(cls, v1_config: V1AssayConfig):
        builder = cls(
            _unwrap(v1_config.client),
            _unwrap(v1_config.pipeline_id),
            v1_config.pipeline_name,
            _unwrap(v1_config.workspace_id),
        )
        builder.targeting = Targeting._from_v1_config(v1_config)
        builder.baseline = SummaryBaseline._from_v1_config(v1_config)
        builder.scheduling = Scheduling._from_v1_config(
            v1_config, builder.baseline._get_baseline_end()
        )
        builder.summarizer = Summarizer._from_v1_config(v1_config)
        builder.window = RollingWindow._from_v1_config(v1_config)

        builder.metric = builder.summarizer.univariate_continuous.metric
        builder.bin_mode = builder.summarizer.univariate_continuous.bin_mode
        builder.aggregation = builder.summarizer.univariate_continuous.aggregation
        builder.bin_weights = builder.summarizer.univariate_continuous.bin_weights

        return builder

    def build(self) -> "AssayV2":
        """Build the AssayV2 object.

        :return: The AssayV2 object.
        """
        from .assay_v2 import AssayV2

        self._validate()

        self.summarizer = Summarizer(
            UnivariateContinuous(
                self.aggregation,
                self.bin_mode,  # type: ignore[arg-type]
                self.metric,
                self.bin_weights,  # type: ignore[arg-type]
            )
        )
        ret = sync_detailed_schedule(
            client=self.client.mlops(),
            body=ScheduleBody(
                name=self.name,
                baseline=self.baseline,  # type: ignore[arg-type]
                scheduling=self.scheduling,
                summarizer=self.summarizer,
                targeting=self.targeting,
                window=self.window,  # type: ignore[arg-type]
            ),
        )

        if ret is None:
            raise Exception(f"Failed to schedule assay. {ret.content}")

        id_ = cast(str, ret.parsed)

        return AssayV2(client=self.client, id=id_)

    def set_name(self, name: str) -> "AssayV2Builder":
        """Set the name of the assay.

        :param name: The name of the assay.

        :return: The AssayV2Builder object.
        """
        self.name = name
        return self

    # TODO: Make workspace_id optional, warn user and grab current workspace?
    def set_pipeline(self, pipeline_name: str, workspace_id: int) -> "AssayV2Builder":
        """Set the pipeline and workspace for the assay.

        :param pipeline_name: The name of the pipeline.
        :param workspace_id: The workspace id.

        :return: The AssayV2Builder object.
        """
        self.targeting.data_origin.pipeline_name = pipeline_name
        self.targeting.data_origin.workspace_id = workspace_id
        return self

    def set_model(self, model_name: str) -> "AssayV2Builder":
        """Set the model name for the assay.

        :param model_name: The name of the model.
        """
        self.targeting.data_origin.model_id = model_name
        return self

    def add_monitoring(
        self,
        field: str,
        indices: List[int],
        warning: Optional[float] = None,
        alert: Optional[float] = None,
    ) -> "AssayV2Builder":
        """Append an iopath to the assay.

        :param field: The field of the iopath.
        :param indices: The indices of the iopath.
        :param warning: The warning threshold.
        :param alert: The alert threshold.

        :return: The AssayV2Builder object.
        """
        thresh = Thresholds(warning=warning, alert=alert)
        dp = DataPath(field, indices, thresh)
        self.targeting.iopath.append(dp)
        return self

    def set_monitoring(
        self,
        field: str,
        indices: List[int],
        warning: Optional[float] = None,
        alert: Optional[float] = None,
    ) -> "AssayV2Builder":
        """Append an iopath to the assay.

        :param field: The field of the iopath.
        :param indices: The indices of the iopath.
        :param warning: The warning threshold.
        :param alert: The alert threshold.

        :return: The AssayV2Builder object.
        """
        thresh = Thresholds(warning=warning, alert=alert)
        dp = DataPath(field, indices, thresh)
        self.targeting.iopath = [dp]
        return self

    def set_baseline(self, start: datetime, end: datetime) -> "AssayV2Builder":
        """Set the baseline for the assay.

        :param start: The start time of the baseline.
        :param end: The end time of the baseline.

        :return: The AssayV2Builder object.
        """
        self.baseline = StaticBaseline([start, end])

        if self.window is None:
            self.set_window_width(end - start)

        return self

    def set_window_width(self, width: Union[timedelta, int]) -> "AssayV2Builder":
        """Set the window width for the assay.

        :param width: The width of the window.

        :return: The AssayV2Builder object.
        """
        width = width if isinstance(width, int) else int(width.total_seconds())
        self.window = RollingWindow(WindowWidthDuration(width))
        return self

    def set_first_run(self, first_run: datetime) -> "AssayV2Builder":
        """Set the first run for the assay.

        :param first_run: The first run time.

        :return: The AssayV2Builder object.
        """
        self.scheduling.first_run = first_run.astimezone()
        return self

    def daily(self, quantity=1) -> "AssayV2Builder":
        """Set the daily run frequency for the assay.

        :param quantity: The quantity of the run frequency.

        :return: The AssayV2Builder object.
        """
        self.scheduling.run_frequency = MLOpsSimpleRunFrequency(
            PGInterval(quantity, IntervalUnit.DAY)
        )
        return self

    def hourly(self, quantity=1) -> "AssayV2Builder":
        """Set the hourly run frequency for the assay.

        :param quantity: The quantity of the run frequency.

        :return: The AssayV2Builder object.
        """
        self.scheduling.run_frequency = MLOpsSimpleRunFrequency(
            PGInterval(quantity, IntervalUnit.HOUR)
        )
        return self

    def weekly(self) -> "AssayV2Builder":
        """Set the weekly run frequency for the assay.

        :return: The AssayV2Builder object.
        """
        self.scheduling.run_frequency = MLOpsSimpleRunFrequency(
            PGInterval(1, IntervalUnit.WEEK)
        )
        return self

    def minutely(self, quantity=1) -> "AssayV2Builder":
        """Set the minutely run frequency for the assay.

        :param quantity: The quantity of the run frequency.

        :return: The AssayV2Builder object.
        """
        self.scheduling.run_frequency = MLOpsSimpleRunFrequency(
            PGInterval(quantity, IntervalUnit.MINUTE)
        )
        return self

    def days_of_data(self, quantity=1) -> "AssayV2Builder":
        """Set the days of data for the assay.

        :param quantity: The quantity of the days of data.

        :return: The AssayV2Builder object.
        """
        self.set_window_width(quantity * 60 * 60 * 24)
        return self

    def minutes_of_data(self, quantity=1) -> "AssayV2Builder":
        """Set the minutes of data for the assay.

        :param quantity: The quantity of the minutes of data.

        :return: The AssayV2Builder object.
        """
        self.set_window_width(quantity * 60)
        return self

    def hours_of_data(self, quantity=1) -> "AssayV2Builder":
        """Set the hours of data for the assay.

        :param quantity: The quantity of the hours of data.

        :return: The AssayV2Builder object.
        """
        self.set_window_width(quantity * 60 * 60)
        return self

    def weeks_of_data(self, quantity=1) -> "AssayV2Builder":
        """Set the weeks of data for the assay.

        :param quantity: The quantity of the weeks of data.

        :return: The AssayV2Builder object.
        """
        self.set_window_width(quantity * 60 * 60 * 24 * 7)
        return self

    def cumulative_aggregation(self) -> "AssayV2Builder":
        """Set a cumulative aggregation for the assay.
        It keeps a cumulative count of the values/percentages
        that fall in each bin.

        :return: The AssayV2Builder object.
        """
        self.aggregation = Aggregation.CUMULATIVE
        return self

    def density_aggregation(self) -> "AssayV2Builder":
        """Set a density aggregation for the assay.
        It counts the number/percentage of values that fall in each bin.

        :return: The AssayV2Builder object.
        """
        self.aggregation = Aggregation.DENSITY
        return self

    def edge_aggregation(self) -> "AssayV2Builder":
        """Set an edge aggregation for the assay.
        It looks at the calculated bin edges instead of how the data is binned.

        :return: The AssayV2Builder object.
        """
        self.aggregation = Aggregation.EDGES
        return self

    def max_diff_metric(self) -> "AssayV2Builder":
        """Set the max difference metric for the assay.
        It measures the maximum difference between the baseline and current distributions
        (as estimated using the bins)

        :return: The AssayV2Builder object.
        """
        self.metric = Metric.MAXDIFF
        return self

    def psi_metric(self) -> "AssayV2Builder":
        """Set the psi metric for the assay.
        It is an entropy-based measure of the difference between distributions.

        :return: The AssayV2Builder object.
        """
        self.metric = Metric.PSI
        return self

    def sum_diff_metric(self) -> "AssayV2Builder":
        """Set the sum difference metric for the assay.
        It sums up the difference of occurrences in each bin between the baseline
        and current distributions.

        :return: The AssayV2Builder object.
        """
        self.metric = Metric.SUMDIFF
        return self

    def no_bins(self) -> "AssayV2Builder":
        """Set no bins for the assay.

        :return: The AssayV2Builder object.
        """
        self.bin_mode = BinModeType0.NONE
        return self

    def equal_bins(self, num: int) -> "AssayV2Builder":
        """Set equal bins for the assay.
        It defines the bins using equally spaced data value ranges, like a histogram.

        :param num: The number of bins.

        :return: The AssayV2Builder object.
        """
        self.bin_mode = BinModeType1(equal=num)
        return self

    def quantile_bins(self, num: int) -> "AssayV2Builder":
        """Set quantile bins for the assay.
        It defines the bins using percentile ranges (each bin holds the same percentage of the baseline data).

        :param num: The number of bins.

        :return: The AssayV2Builder object.
        """
        self.bin_mode = BinModeType2(num)
        return self

    def set_bin_weights(self, weights: List[float]) -> "AssayV2Builder":
        """Set the bin weights for the assay.

        :param weights: The bin weights.

        :return: The AssayV2Builder object.
        """
        if isinstance(self.bin_mode, BinModeType1) and self.bin_mode.equal != len(
            weights
        ):
            raise Exception(
                f"Improperly configured bin weights! There are {self.bin_mode.equal} bins but received {len(weights)} weights"
            )
        elif isinstance(self.bin_mode, BinModeType2) and self.bin_mode.quantile != len(
            weights
        ):
            raise Exception(
                f"Improperly configured bin weights! There are {self.bin_mode.quantile} bins but received {len(weights)} weights"
            )

        self.bin_weights = weights
        return self

    def set_aggregation(
        self, aggregation=Union[str, Aggregation, V1Aggregation]
    ) -> "AssayV2Builder":
        """Set the aggregation for the assay.

        :param aggregation: The aggregation.

        :return: The AssayV2Builder object.
        """
        self.aggregation = Aggregation[aggregation.upper()]
        return self

    def set_metric(self, metric=Union[str, Metric, V1Metric]) -> "AssayV2Builder":
        """Set the metric for the assay.

        :param metric: The metric.

        :return: The AssayV2Builder object.
        """
        self.metric = Metric[metric.upper()]
        return self

    def set_locations(self, locations=List[str]) -> "AssayV2Builder":
        """Set the data origin locations for the assay.

        :param locations: The locations.

        :return: The AssayV2Builder object.
        """
        self.targeting.data_origin.locations = locations
        return self

    def add_locations(self, location: str) -> "AssayV2Builder":
        """Append a location to the data origin for the assay.

        :param location: The location.

        :return: The AssayV2Builder object.
        """
        if self.targeting.data_origin.locations is not None and not isinstance(
            self.targeting.data_origin.locations, Unset
        ):
            self.targeting.data_origin.locations.append(location)
        else:
            self.targeting.data_origin.locations = [location]
        return self

    def preview(
        self, start: datetime, end: datetime, include_failures=False
    ) -> PreviewResultList:
        """Preview the assay. This is used for interactive runs that are not saved to the database.

        :param start: The start time.
        :param end: The end time.
        :param include_failures: Whether to include failures.

        :return: The AssayV2Builder object.
        """
        self._validate()

        if not isinstance(end, datetime):
            raise Exception(
                "Previews require an end time to be set. See builder.add_run_until()."
            )

        self.summarizer = Summarizer(
            UnivariateContinuous(
                self.aggregation,
                self.bin_mode,  # type: ignore[arg-type]
                self.metric,
                self.bin_weights,  # type: ignore[arg-type]
            )
        )

        body = PreviewBody(
            self.baseline,  # type: ignore[arg-type]
            preview_start=start,
            preview_end=end,
            scheduling=self.scheduling,
            summarizer=self.summarizer,
            targeting=self.targeting,
            window=_unwrap(self.window),
        )
        ret = sync_detailed_preview(client=self.client.mlops(), body=body)

        if ret.parsed is None:
            raise Exception("An error occurred while previewing assay: ", ret.content)

        arr = [
            PreviewResult(x, self)
            for x in ret.parsed
            if include_failures or len(x.summaries.additional_properties) > 0
        ]
        return PreviewResultList(arr, self)

    def _get_iopath(self) -> str:
        return self.targeting._get_iopath()
