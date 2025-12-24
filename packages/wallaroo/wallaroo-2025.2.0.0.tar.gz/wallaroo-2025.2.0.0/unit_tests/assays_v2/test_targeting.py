import pytest

from wallaroo.assay_config import AssayConfig as V1AssayConfig
from wallaroo.assays_v2.targeting import Targeting
from wallaroo.wallaroo_ml_ops_api_client.models import DataOrigin, DataPath, Thresholds
from wallaroo.wallaroo_ml_ops_api_client.types import UNSET


@pytest.fixture(scope="module")
def data_origin():
    return DataOrigin(
        pipeline_id=1,
        pipeline_name="some-pipeline",
        workspace_id=1,
        workspace_name="some-workspace",
        model_id="some-model",
    )


@pytest.fixture(scope="module")
def data_path():
    return DataPath(
        field="out.variable",
        indexes=[1, 2, 3],
        thresholds=Thresholds(alert=0.5, warning=0.3),
    )


def test_get_iopath(data_origin, data_path):
    targeting_instance = Targeting(data_origin=data_origin, iopath=[data_path])
    result = targeting_instance._get_iopath()
    assert result == "out.variable.1"


@pytest.mark.parametrize("indexes", [None, UNSET])
def test_get_iopath_if_indexes_not_set(data_origin, indexes):
    data_path = DataPath(
        field="out.variable",
        indexes=indexes,
        thresholds=Thresholds(alert=0.5, warning=0.3),
    )
    targeting_instance = Targeting(data_origin=data_origin, iopath=[data_path])
    result = targeting_instance._get_iopath()
    assert result == "out.variable"


@pytest.mark.parametrize("locations", [None, ["edge-location-1"]])
def test_from_v1_config(mocker, locations):
    v1_config = mocker.Mock(
        spec=V1AssayConfig,
        window=mocker.Mock(path="output variable 0", model_name="model_name"),
    )
    v1_config.alert_threshold = 0.5
    v1_config.warning_threshold = 0.3
    v1_config.pipeline_id = 1
    v1_config.pipeline_name = "pipeline_name"
    v1_config.workspace_id = 1
    v1_config.workspace_name = "some-workspace"
    v1_config.window.locations = locations

    result = Targeting._from_v1_config(v1_config)

    assert result.data_origin == DataOrigin(
        pipeline_id=1,
        pipeline_name="pipeline_name",
        workspace_id=1,
        workspace_name="some-workspace",
        model_id="model_name",
        locations=locations,
    )
    assert result.iopath[0].field == "out.variable"
    assert result.iopath[0].indexes == [0]
    assert result.iopath[0].thresholds == Thresholds(alert=0.5, warning=0.3)


def test_from_v1_config_raise_error_if_workspace_id_is_none(mocker):
    v1_config = mocker.Mock(
        spec=V1AssayConfig,
        window=mocker.Mock(path="output variable 0", model_name="model_name"),
    )
    v1_config.alert_threshold = 0.5
    v1_config.warning_threshold = 0.3
    v1_config.pipeline_id = 1
    v1_config.pipeline_name = "pipeline_name"
    v1_config.workspace_id = None

    with pytest.raises(Exception, match="Expected a value in forced unwrap"):
        _ = Targeting._from_v1_config(v1_config)


@pytest.mark.parametrize(
    "path,expected_field,expected_indexes",
    [
        ("out variable 0", "out.variable", [0]),  # 3 parts
        ("out variable", "out.variable", None),  # 2 parts
    ],
)
def test_from_v1_config_path_parsing(mocker, path, expected_field, expected_indexes):
    v1_config = mocker.Mock(
        spec=V1AssayConfig,
        window=mocker.Mock(path=path, model_name="model_name"),
    )
    v1_config.alert_threshold = 0.5
    v1_config.warning_threshold = 0.3
    v1_config.pipeline_id = 1
    v1_config.pipeline_name = "pipeline_name"
    v1_config.workspace_id = 1
    v1_config.workspace_name = "some-workspace"
    v1_config.window.locations = None

    result = Targeting._from_v1_config(v1_config)

    assert result.iopath[0].field == expected_field
    assert result.iopath[0].indexes == expected_indexes
