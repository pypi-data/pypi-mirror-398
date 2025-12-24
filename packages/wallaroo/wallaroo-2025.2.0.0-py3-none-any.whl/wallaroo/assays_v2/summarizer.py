"""This module features the Summarizer class that configures summarizers."""

from typing import Union, cast

from wallaroo.assay_config import (
    AssayConfig as V1AssayConfig,
    BinMode as V1BinMode,
    Metric as V1Metric,
    UnivariateContinousSummarizerConfig as V1Summarizer,
)
from wallaroo.utils import _unwrap
from wallaroo.wallaroo_ml_ops_api_client.models.aggregation import Aggregation
from wallaroo.wallaroo_ml_ops_api_client.models.bin_mode_type_0 import BinModeType0
from wallaroo.wallaroo_ml_ops_api_client.models.bin_mode_type_1 import BinModeType1
from wallaroo.wallaroo_ml_ops_api_client.models.bin_mode_type_2 import BinModeType2
from wallaroo.wallaroo_ml_ops_api_client.models.bin_mode_type_3 import BinModeType3
from wallaroo.wallaroo_ml_ops_api_client.models.bin_mode_type_4 import BinModeType4
from wallaroo.wallaroo_ml_ops_api_client.models.metric import Metric
from wallaroo.wallaroo_ml_ops_api_client.models.summarizer_type_0 import (
    SummarizerType0 as UnivariateSummarizer,
)
from wallaroo.wallaroo_ml_ops_api_client.models.univariate_continuous import (
    UnivariateContinuous,
)


class Summarizer(UnivariateSummarizer):
    """This class represents a summarizer."""

    def _get_display_row(self) -> str:
        bin_mode_str = None
        if isinstance(self.univariate_continuous.bin_mode, BinModeType0):
            bin_mode_str = self.univariate_continuous.bin_mode.name
        elif isinstance(self.univariate_continuous.bin_mode, BinModeType1):
            bin_mode_str = f"{self.univariate_continuous.bin_mode.equal} Equal bins"
        elif isinstance(self.univariate_continuous.bin_mode, BinModeType2):
            bin_mode_str = (
                f"{self.univariate_continuous.bin_mode.quantile} Quantile bins"
            )
        elif isinstance(self.univariate_continuous.bin_mode, BinModeType3):
            bin_mode_str = f"{self.univariate_continuous.bin_mode.quantile_with_explicit_outliers} Quantile bins"
        elif isinstance(self.univariate_continuous.bin_mode, BinModeType4):
            bin_mode_str = f"{self.univariate_continuous.bin_mode.provided}"

        # TODO: Would be nice to wrap this in a <summary> and show the actual bins underneath.
        return f"""
        <tr><td>Bin Mode</td><td>{bin_mode_str}</td></tr>
        {f"<tr><td>Bin Weights</td><td>{self.univariate_continuous.bin_weights}</td></tr>" if self.univariate_continuous.bin_weights else ""}
        <tr><td>Aggregation</td><td>{self.univariate_continuous.aggregation.value}</td></tr>
        <tr><td>Metric</td><td>{self.univariate_continuous.metric.value}</td></tr>
        """

    @classmethod
    def _from_v1_config(cls, v1_config: V1AssayConfig) -> "Summarizer":
        config_summarizer = cast(V1Summarizer, v1_config.summarizer)
        return Summarizer.from_v1_summarizer(config_summarizer)

    @classmethod
    def from_v1_summarizer(cls, summarizer: V1Summarizer) -> "Summarizer":
        """Create a Summarizer from a V1Summarizer.

        :param summarizer: The v1 summarizer.

        :return: The Summarizer.
        """
        agg = summarizer.aggregation
        v1_mode = summarizer.bin_mode
        v1_bin_count = summarizer.num_bins
        v1_edges = summarizer.provided_edges
        v1_weights = summarizer.bin_weights

        # TODO: Handle add_explicit_edges
        v2_mode = cast(
            Union[BinModeType0, BinModeType1, BinModeType2, BinModeType4],
            BinModeType0.NONE,
        )
        if v1_mode == V1BinMode.NONE:
            v2_mode = BinModeType0.NONE
        elif v1_mode == V1BinMode.EQUAL:
            v2_mode = BinModeType1(v1_bin_count)
        elif v1_mode == V1BinMode.QUANTILE:
            v2_mode = BinModeType2(v1_bin_count)
        elif v1_mode == V1BinMode.PROVIDED:
            v2_mode = BinModeType4(_unwrap(v1_edges))

        metric = V1Metric[summarizer.metric.name]

        return cls(
            univariate_continuous=UnivariateContinuous(
                Aggregation[agg.name], v2_mode, Metric[metric.name], v1_weights
            )
        )
