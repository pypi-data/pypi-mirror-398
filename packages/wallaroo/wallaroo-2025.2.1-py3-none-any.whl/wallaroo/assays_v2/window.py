"""This module features the RollingWindow class that configures the rolling window."""

from wallaroo.assay_config import (
    AssayConfig as V1AssayConfig,
)
from wallaroo.utils import _unwrap
from wallaroo.wallaroo_ml_ops_api_client.models.rolling_window import (
    RollingWindow as MLOpsRollingWindow,
)
from wallaroo.wallaroo_ml_ops_api_client.models.window_width_duration import (
    WindowWidthDuration,
)


class RollingWindow(MLOpsRollingWindow):
    """This class represents a rolling window configuration."""

    @classmethod
    def _from_v1_config(cls, v1_config: V1AssayConfig) -> "RollingWindow":
        dur = None
        (count, unit) = v1_config.window.width.split()
        if unit in ("minutes", "minute"):
            dur = int(count) * 60
        elif unit in ("hours", "hour"):
            dur = int(count) * 60 * 60
        elif unit in ("days", "day"):
            dur = int(count) * 60 * 60 * 24
        elif unit in ("weeks", "week"):
            dur = int(count) * 60 * 60 * 24 * 7

        return RollingWindow(width=WindowWidthDuration(seconds=_unwrap(dur)))

    def _get_display_row(self) -> str:
        return f"""
        <tr><td>Window Width</td><td>{self.width.seconds} seconds</td></tr>
        """
