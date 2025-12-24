"""This module features the Scheduling class that configures scheduling."""

from datetime import datetime, timezone
from typing import Optional, cast

from wallaroo.assay_config import (
    AssayConfig as V1AssayConfig,
)
from wallaroo.wallaroo_ml_ops_api_client.models.interval_unit import IntervalUnit
from wallaroo.wallaroo_ml_ops_api_client.models.pg_interval import PGInterval
from wallaroo.wallaroo_ml_ops_api_client.models.run_frequency_type_1 import (
    RunFrequencyType1 as MLOpsSimpleRunFrequency,
)
from wallaroo.wallaroo_ml_ops_api_client.models.scheduling import (
    Scheduling as MLOpsScheduling,
)

fmt: str = "%Y-%d-%b %H:%M:%S"


class Scheduling(MLOpsScheduling):
    """This class represents a scheduling configuration."""

    @classmethod
    def _from_v1_config(
        cls, v1_config: V1AssayConfig, baseline_end_at: Optional[datetime]
    ) -> "Scheduling":
        interval = (
            v1_config.window.interval
            if v1_config.window.interval
            else v1_config.window.width
        )

        first_run = (
            v1_config.window.start
            if v1_config.window.start
            else (baseline_end_at if baseline_end_at else datetime.now(timezone.utc))
        )

        run_frequency = cast(Optional[PGInterval], None)
        (count, unit) = interval.split()
        if unit in ("minutes", "minute"):
            run_frequency = PGInterval(quantity=int(count), unit=IntervalUnit.MINUTE)
        elif unit in ("hours", "hour"):
            run_frequency = PGInterval(quantity=int(count), unit=IntervalUnit.HOUR)
        elif unit in ("days", "day"):
            run_frequency = PGInterval(quantity=int(count), unit=IntervalUnit.DAY)
        elif unit in ("weeks", "week"):
            run_frequency = PGInterval(quantity=int(count), unit=IntervalUnit.WEEK)

        if run_frequency is None:
            raise Exception(
                f"Failed to parse the run frequency for this assay with interval: `{interval}`"
            )

        return Scheduling(
            first_run=first_run,
            run_frequency=MLOpsSimpleRunFrequency(simple_run_frequency=run_frequency),
            # Run Until from a product persp. is only used for previews.
            # end=v1_config.run_until,
        )

    def _get_display_row(self) -> str:
        quantity = self.run_frequency.simple_run_frequency.quantity  # type: ignore[union-attr]
        unit = self.run_frequency.simple_run_frequency.unit  # type: ignore[union-attr]
        return f"""
        <tr><td>First Run</td><td>{self.first_run.strftime(fmt)}</td></tr>
        {f"<tr><td>End Run</td><td>{self.end.strftime(fmt)}</td></tr>" if self.end else ""}
        {f"<tr><td>Run Frequency</td><td>{quantity} {unit}</td></tr>"}
        """
