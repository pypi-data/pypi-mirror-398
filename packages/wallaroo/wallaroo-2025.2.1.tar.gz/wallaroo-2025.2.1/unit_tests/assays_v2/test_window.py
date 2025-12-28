import pytest

from wallaroo.assay_config import AssayConfig as V1AssayConfig
from wallaroo.assays_v2.window import RollingWindow


@pytest.mark.parametrize(
    "width, expected",
    [("5 minutes", 300), ("1 hour", 3600), ("2 days", 172800), ("3 weeks", 1814400)],
)
def test_from_v1_config(width, expected, mocker):
    v1_config = mocker.Mock(spec=V1AssayConfig, window=mocker.Mock(width=width))
    result = RollingWindow._from_v1_config(v1_config)

    assert result.width.seconds == expected
