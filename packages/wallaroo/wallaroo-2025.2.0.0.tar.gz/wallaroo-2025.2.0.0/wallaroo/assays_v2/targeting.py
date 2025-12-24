"""This module features the Targeting class that configures targeting."""

from typing import cast

from wallaroo.assay_config import (
    AssayConfig as V1AssayConfig,
    WindowConfig,
)
from wallaroo.utils import _unwrap
from wallaroo.wallaroo_ml_ops_api_client.models.data_origin import DataOrigin
from wallaroo.wallaroo_ml_ops_api_client.models.data_path import DataPath
from wallaroo.wallaroo_ml_ops_api_client.models.targeting import (
    Targeting as MLOpsTargeting,
)
from wallaroo.wallaroo_ml_ops_api_client.models.thresholds import Thresholds
from wallaroo.wallaroo_ml_ops_api_client.types import Unset


class Targeting(MLOpsTargeting):
    """This class represents a targeting configuration."""

    @classmethod
    def _from_v1_config(cls, v1_config: V1AssayConfig) -> "Targeting":
        parsed_path = _unwrap(v1_config.window.path).split()
        locations = v1_config.window.locations or None
        prefix = "in" if parsed_path[0] == "input" else "out"

        model_name = v1_config.window.model_name
        thresh = Thresholds(
            alert=v1_config.alert_threshold, warning=v1_config.warning_threshold
        )
        do = DataOrigin(
            _unwrap(v1_config.pipeline_id),
            v1_config.pipeline_name,
            _unwrap(v1_config.workspace_id),
            _unwrap(v1_config.workspace_name),
            locations=locations,
            model_id=model_name,
        )
        dp = DataPath(
            field=f"{prefix}.{parsed_path[1]}",
            indexes=[int(parsed_path[2])]
            if len(parsed_path) > 2
            else None,  # if inference result is a list, we need to parse the index from provided path, otherwise it's a scalar and `indexes` must be `None`
            thresholds=thresh,
        )
        return cls(do, [dp])

    @classmethod
    def from_v1_args(
        cls,
        window: WindowConfig,
        alert_threshold: float,
        warning_threshold: float,
        pipeline_id: str,
        pipeline_name: str,
        workspace_id: str,
        workspace_name: str,
    ) -> "Targeting":
        parsed_path = _unwrap(window.path).split()
        locations = window.locations or None
        prefix = "in" if parsed_path[0] == "input" else "out"

        model_name = window.model_name
        thresh = Thresholds(alert=alert_threshold, warning=warning_threshold)
        do = DataOrigin(
            cast(int, pipeline_id),
            pipeline_name,
            cast(int, workspace_id),
            workspace_name,
            locations=locations,
            model_id=model_name,
        )
        dp = DataPath(
            field=f"{prefix}.{parsed_path[1]}",
            indexes=[int(parsed_path[2])]
            if len(parsed_path) > 2
            else None,  # if inference result is a list, we need to parse the index from provided path, otherwise it's a scalar and `indexes` must be `None`
            thresholds=thresh,
        )
        return cls(do, [dp])

    def _get_iopath(self) -> str:
        """Returns the legacy iopath"""
        suffix = (
            ""
            if self.iopath[0].indexes is None  # if the inference result is a scalar
            or isinstance(self.iopath[0].indexes, Unset)
            else "." + str(_unwrap(self.iopath[0].indexes)[0])
        )
        return f"{self.iopath[0].field}{suffix}"

    def _get_display_row(self) -> str:
        return f"""
        <tr><td>Pipeline</td><td>{self.data_origin.pipeline_name}</td></tr>
        {f"<tr><td>Model ID</td><td>{self.data_origin.model_id}</td></tr>" if self.data_origin.model_id else ""}
        <tr><td>Workspace ID</td><td>{self.data_origin.workspace_id}</td></tr>
        """
