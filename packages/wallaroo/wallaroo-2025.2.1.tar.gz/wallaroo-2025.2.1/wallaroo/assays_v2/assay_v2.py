"""This module features the AssayV2 class that configures assays and retrieves results via the MLOps API."""

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union, cast
from uuid import UUID

from wallaroo.assays_v2.assay_result_v2 import AssayResultsList, AssayResultV2
from wallaroo.assays_v2.baseline import StaticBaseline, SummaryBaseline
from wallaroo.assays_v2.scheduling import Scheduling
from wallaroo.assays_v2.summarizer import Summarizer
from wallaroo.assays_v2.targeting import Targeting
from wallaroo.assays_v2.window import RollingWindow
from wallaroo.object import Object
from wallaroo.utils import _ensure_tz
from wallaroo.wallaroo_ml_ops_api_client.api.assays.get_by_id import (
    GetByIdBody,
    sync as sync_get_by_id,
)
from wallaroo.wallaroo_ml_ops_api_client.api.assays.get_results import (
    GetResultsBody,
    sync_detailed as sync_detailed_results,
)
from wallaroo.wallaroo_ml_ops_api_client.api.assays.set_active import (
    SetActiveBody,
    sync_detailed as sync_detailed_set_active,
)
from wallaroo.wallaroo_ml_ops_api_client.models import (
    BaselineType0 as MLOpsSummaryBaseline,
    BaselineType1 as MLOpsStaticBaseline,
)
from wallaroo.wallaroo_ml_ops_api_client.models.assay_v2 import AssayV2 as MLOpsAssayV2
from wallaroo.wallaroo_ml_ops_api_client.models.scheduling import (
    Scheduling as MLOpsScheduling,
)
from wallaroo.wallaroo_ml_ops_api_client.models.summarizer_type_0 import (
    SummarizerType0 as UnivariateSummarizer,
)
from wallaroo.wallaroo_ml_ops_api_client.models.targeting import (
    Targeting as MLOpsTargeting,
)
from wallaroo.workspace import Workspace

if TYPE_CHECKING:
    # Imports that happen below in methods to fix circular import dependency
    # issues need to also be specified here to satisfy mypy type checking.
    from wallaroo.client import Client

    from .assay_v2_builder import AssayV2Builder


class AssayV2(Object):
    """This class helps configure assays and retrieve results via the MLOps API.

    Attributes:
        - id: The ID of the assay.
    """

    def __init__(self, client: "Client", id: str) -> None:
        """Initializes the AssayV2 object."""
        assert client is not None
        self._client = client
        self.id = id
        super().__init__(gql_client=client._gql_client, data={}, fetch_first=True)

    def _fill(self, data) -> None:
        # Can't violate the Liskov principle, so we can rehydrate the typings here.
        data = MLOpsAssayV2.from_dict(data)
        self.id = str(data.id)
        self.name = data.name
        self.active = data.active

        if hasattr(data, "window"):
            self.window = RollingWindow.from_dict(data.window.to_dict())

        if hasattr(data, "baseline"):
            if isinstance(data.baseline, MLOpsStaticBaseline):
                self.baseline = cast(
                    Union[StaticBaseline, SummaryBaseline],
                    StaticBaseline.from_dict(data.baseline.to_dict()),
                )

            elif isinstance(data.baseline, MLOpsSummaryBaseline):
                self.baseline = SummaryBaseline.from_dict(data.baseline.to_dict())

        if hasattr(data, "scheduling"):
            if isinstance(data.scheduling, MLOpsScheduling):
                self.scheduling = Scheduling.from_dict(data.scheduling.to_dict())

        if hasattr(data, "summarizer"):
            if isinstance(data.summarizer, UnivariateSummarizer):
                self.summarizer = Summarizer.from_dict(data.summarizer.to_dict())

        if hasattr(data, "targeting"):
            if isinstance(data.targeting, MLOpsTargeting):
                self.targeting = Targeting.from_dict(data.targeting.to_dict())

        self.created_at = data.created_at
        self.updated_at = data.updated_at

    def _fetch_attributes(self) -> Dict[str, Any]:
        ret = sync_get_by_id(
            client=self._client.mlops(), body=GetByIdBody(UUID(self.id))
        )
        if ret is None:
            raise Exception(f"Failed to fetch assay {self.id}")
        return ret.to_dict()

    def results(
        self,
        start: datetime,
        end: datetime,
        include_failures: bool = False,
        workspace_id: Optional[int] = None,
    ) -> AssayResultsList:
        """Retrieves the results of the assay.

        :param start: The start time.
        :param end: The end time.
        :param include_failures: Whether to include failures.
        :param workspace_id: The workspace ID.

        :return: The assay results.
        """

        ret = sync_detailed_results(
            client=self._client.mlops(),
            body=GetResultsBody(
                id=UUID(self.id),
                start=_ensure_tz(start),
                end=_ensure_tz(end),
                workspace_id=workspace_id,
            ),
        )
        if ret.parsed is None:
            raise Exception("An error occurred while getting assay results: ", ret)

        return AssayResultsList(
            [
                AssayResultV2(self, x)
                for x in ret.parsed
                if include_failures or len(x.summaries.additional_properties) > 0  # type: ignore[union-attr]
            ],
            self,
        )

    def set_active(self, active: bool) -> "AssayV2":
        """Sets the active status of the assay.

        :param active: Whether the assay is active.

        :return: The AssayV2 object.
        """
        ret = sync_detailed_set_active(
            client=self._client.mlops(),
            body=SetActiveBody(active, UUID(self.id)),
        )

        if ret.status_code != 200:
            verb = "resume" if active is True else "pause"
            raise Exception(f"Failed to {verb} assay. ", ret.content)

        self._rehydrate()
        return self

    def pause(self) -> "AssayV2":
        """Pauses an assay.
        Note: this only pauses future scheduled runs - historical calculations will still be computed.
        """
        self.set_active(False)
        self._rehydrate()
        return self

    def resume(self) -> "AssayV2":
        """Resumes a previously-paused assay."""
        self.set_active(True)
        self._rehydrate()
        return self

    @staticmethod
    def builder(
        client: "Client", pipeline_id, pipeline_name: str, workspace_id: int
    ) -> "AssayV2Builder":
        """Return an AssayV2Builder.

        :param client: The client object.
        :param pipeline_name: The name of the pipeline.
        :param workspace_id: The workspace id.

        :return: The AssayV2Builder object.
        """
        from .assay_v2_builder import AssayV2Builder

        return AssayV2Builder(client, pipeline_id, pipeline_name, workspace_id)

    def _next_run(self) -> Any:
        from wallaroo.wallaroo_ml_ops_api_client.api.assays.get_next_run import (
            GetNextRunBody,
            sync_detailed,
        )

        ret = sync_detailed(
            client=self._client.mlops(), body=GetNextRunBody(UUID(self.id))
        )

        if ret.parsed is None:
            raise Exception(ret.content)

        return ret.parsed

    def _get_iopath(self) -> str:
        return self.targeting._get_iopath()

    def _repr_html_(self) -> str:
        self._rehydrate()
        fmt = self._client._time_format
        next_run_data = self._next_run()
        workspace_name = Workspace(
            self._client, {"id": self.targeting.data_origin.workspace_id}
        ).name()
        return f"""<table>
          <tr><th>Field</th><th>Value</th></tr>
          <tr><td>ID</td><td>{self.id}</td></tr>
          <tr><td>Name</td><td>{self.name}</td></tr>
          <tr><td>Active</td><td>{self.active}</td></tr>
          {self.targeting._get_display_row()}
          <tr><td>Workspace Name</td><td>{workspace_name}</td></tr>
          {self.baseline._get_display_row()}
          {self.window._get_display_row()}
          {self.scheduling._get_display_row()}
          {self.summarizer._get_display_row()}
          <tr><td>Last Run</td><td>{next_run_data.last_run.astimezone(timezone.utc).strftime(fmt) if next_run_data.last_run else None}</td></tr>
          <tr><td>Next Run</td><td>{next_run_data.next_run.astimezone(timezone.utc).strftime(fmt) if next_run_data.next_run else None}</td></tr>
          <tr><td>Created At</td><td>{self.created_at.strftime(fmt)}</td></tr>
          <tr><td>Updated At</td><td>{self.updated_at.strftime(fmt)}</td></tr>
        </table>"""


class AssayV2List(List[AssayV2]):
    """This class represents a list of assays."""

    def _repr_html_(self) -> str:
        def row(assay: AssayV2) -> str:
            next_run_data = assay._next_run()
            fmt = assay._client._time_format
            monitored_fields = None
            workspace_name = Workspace(
                assay._client, {"id": assay.targeting.data_origin.workspace_id}
            ).name()
            if isinstance(assay.baseline, SummaryBaseline):
                monitored_fields = list(assay.baseline.summary.to_dict().keys())
            return f"""
            <tr>
              <td>{assay.id}</td>
              <td>{assay.name}</td>
              <td>{assay.active}</td>
              <td>{assay.targeting.data_origin.pipeline_name}</td>
              <td>{assay.targeting.data_origin.workspace_id}</td>
              <td>{workspace_name}</td>
              <td>{monitored_fields}</td>
              <td>{next_run_data.last_run.astimezone(timezone.utc).strftime(fmt) if next_run_data.last_run else None}</td>
              <td>{next_run_data.next_run.astimezone(timezone.utc).strftime(fmt) if next_run_data.next_run else None}</td>
              <td>{assay.created_at.strftime(fmt)}</td>
              <td>{assay.updated_at.strftime(fmt)}</td>
            </tr>
            """

        fields = [
            "id",
            "name",
            "active",
            "pipeline",
            "workspace id",
            "workspace name",
            "monitored fields",
            "last_run",
            "next_run",
            "created_at",
            "updated_at",
        ]

        if not self:
            return "(no assays)"
        else:
            return (
                "<table>"
                + "<tr><th>"
                + "</th><th>".join(fields)
                + "</th></tr>"
                + ("".join([row(p) for p in self]))
                + "</table>"
            )
