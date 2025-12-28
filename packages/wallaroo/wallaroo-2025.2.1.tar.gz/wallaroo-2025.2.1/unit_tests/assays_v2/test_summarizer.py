import pytest

from wallaroo.assay_config import (
    AssayConfig as V1AssayConfig,
    BinMode as V1BinMode,
    Metric as V1Metric,
    UnivariateContinousSummarizerConfig as V1Summarizer,
)
from wallaroo.assays_v2.summarizer import Summarizer
from wallaroo.wallaroo_ml_ops_api_client.models import (
    Aggregation,
    BinModeType0,
    BinModeType1,
    BinModeType2,
    BinModeType4,
    Metric,
    UnivariateContinuous,
)


@pytest.mark.parametrize(
    "v1_bin_mode, expected_bin_mode",
    [
        (V1BinMode.NONE, BinModeType0.NONE),
        (V1BinMode.EQUAL, BinModeType1(10)),
        (V1BinMode.QUANTILE, BinModeType2(10)),
        (V1BinMode.PROVIDED, BinModeType4([1, 2, 3, 4, 5])),
    ],
)
def test_from_v1_config(mocker, v1_bin_mode, expected_bin_mode):
    v1_config = mocker.Mock(spec=V1AssayConfig)
    bin_weights = [1, 2, 3, 4, 5]
    v1_config.summarizer = V1Summarizer(
        aggregation=Aggregation.EDGES,
        bin_mode=v1_bin_mode,
        num_bins=10,
        provided_edges=[1, 2, 3, 4, 5],
        bin_weights=bin_weights,
        metric=V1Metric.MAXDIFF,
    )

    summarizer = Summarizer._from_v1_config(v1_config)

    assert isinstance(summarizer.univariate_continuous, UnivariateContinuous)
    assert summarizer.univariate_continuous.aggregation == Aggregation.EDGES
    assert summarizer.univariate_continuous.bin_mode == expected_bin_mode
    assert summarizer.univariate_continuous.metric == Metric.MAXDIFF
    assert summarizer.univariate_continuous.bin_weights == bin_weights


def test_from_v1_config_raise_error_if_provided_edges_is_none_and_bin_mode_is_provided(
    mocker,
):
    v1_config = mocker.Mock(spec=V1AssayConfig)
    v1_config.summarizer = V1Summarizer(
        aggregation=Aggregation.EDGES,
        bin_mode=V1BinMode.PROVIDED,
        num_bins=10,
        provided_edges=None,
        bin_weights=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
        metric=V1Metric.MAXDIFF,
    )

    with pytest.raises(Exception, match="Expected a value in forced unwrap"):
        _ = Summarizer._from_v1_config(v1_config)
