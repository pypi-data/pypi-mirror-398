from __future__ import annotations

import json
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional

import gql
from dateutil import parser as dateparse

from wallaroo.task import Task, TaskList
from wallaroo.workspace import Workspace

from . import queries
from .object import (
    DehydratedValue,
    Object,
    RequiredAttributeMissing,
    rehydrate,
    value_if_present,
)

if TYPE_CHECKING:
    # Imports that happen below in methods to fix circular import dependency
    # issues need to also be specified here to satisfy mypy type checking.
    from .client import Client


class Orchestration(Object):
    """An Orchestration object that represents some user-defined code that has been packaged into a container and can be deployed."""

    def __init__(self, client: Client, data: Dict[str, Any]) -> None:
        self.client = client

        super().__init__(
            gql_client=client._gql_client,
            data=data,
        )

    def _fill(self, data: Dict[str, Any]) -> None:
        for required_attribute in ["id"]:
            if required_attribute not in data:
                raise RequiredAttributeMissing(
                    self.__class__.__name__, required_attribute
                )
        # Required
        self._id = data["id"]
        # Optional
        self._name = value_if_present(data, "name")
        self._file_name = value_if_present(data, "file_name")
        self._owner_id = value_if_present(data, "owner_id")
        self._sha = value_if_present(data, "sha")
        self._status = value_if_present(data, "status")
        self._task_id = value_if_present(data, "task_id")
        self._workspace_id = value_if_present(data, "workspace_id")

        self._created_at: datetime | DehydratedValue = (
            dateparse.isoparse(data["created_at"])
            if "created_at" in data
            else DehydratedValue()
        )

        self._updated_at: datetime | DehydratedValue = (
            dateparse.isoparse(data["updated_at"])
            if "updated_at" in data
            else DehydratedValue()
        )

    def _fetch_attributes(self) -> Dict[str, Any]:
        return self._gql_client.execute(
            gql.gql(queries.named("orch/GetOrchestration")), {"id": str(self._id)}
        )["orchestration_by_pk"]

    @staticmethod
    def list_orchestrations(
        client: Client, workspace_id: Optional[int] = None
    ) -> List[Orchestration]:
        from wallaroo.wallaroo_ml_ops_api_client.api.orchestration.orchestration_list_all import (
            sync,
        )
        from wallaroo.wallaroo_ml_ops_api_client.models.list_all_orchestrations_request import (
            ListAllOrchestrationsRequest,
        )

        res = sync(
            client=client.mlops(),
            body=ListAllOrchestrationsRequest(
                task_run_status=[],
                workspace_ids=[workspace_id] if workspace_id is not None else [],
            ),
        )

        if res is None or res.orchestrations is None:
            raise Exception("Failed to list orchestrations")

        return OrchestrationList(
            [
                Orchestration(client=client, data=v.orchestration.to_dict())
                for v in res.orchestrations
            ]
        )

    @staticmethod
    def upload(
        client: Client,
        name: Optional[str] = None,
        bytes_buffer: Optional[bytes] = None,
        path: Optional[str] = None,
        file_name: Optional[str] = None,
    ) -> Orchestration:
        from io import BytesIO
        from os.path import basename

        from wallaroo.wallaroo_ml_ops_api_client.api.orchestration.orchestration_upload import (
            sync_detailed as sync,
        )
        from wallaroo.wallaroo_ml_ops_api_client.models import (
            OrchestrationUploadBody,
            UploadOrchestrationRequest,
        )
        from wallaroo.wallaroo_ml_ops_api_client.types import File

        upload_input = None

        # If bytes are provided directly, use that.
        if bytes_buffer is not None:
            upload_input = BytesIO(bytes_buffer)

        # If a path is provided, use that.
        if path is not None:
            upload_input = BytesIO(open(path, "rb").read())
            file_name = basename(path)

        if upload_input is None:
            raise OrchestrationMissingFile()

        # TODO: Detect filetype and reject non-zip.
        file = File(
            payload=upload_input,
            file_name=file_name or "_",
            mime_type="application/octet-stream",
        )
        metadata = UploadOrchestrationRequest.from_dict(
            {"workspace_id": client.get_current_workspace().id(), "name": name}
        )
        u = OrchestrationUploadBody(file, metadata)

        ret = sync(client=client.mlops(), body=u)

        if ret.parsed is None:
            raise OrchestrationUploadFailed(
                "Internal service error. " + str(ret.content)
            )

        orch = Orchestration(client, dict({"id": ret.parsed.id}))
        orch._rehydrate()
        return orch

    def run_once(
        self,
        name: Optional[str],
        json_args: Dict[Any, Any] = {},
        timeout: Optional[int] = None,
        debug: Optional[bool] = False,
    ):
        """Runs this Orchestration once.

        :param: name str A descriptive identifier for this run.
        :param: json_args Dict[Any, Any] A JSON object containing deploy-specific arguments.
        :param: timeout Optional[int] A timeout in seconds. Any instance of this orchestration that is running for longer than this specified time will be automatically killed.
        :param: debug Optional[bool] Produce extra debugging output about the run
        :return: A metadata object associated with the deploy Task
        """
        from wallaroo.wallaroo_ml_ops_api_client.api.task.oneshot import sync_detailed
        from wallaroo.wallaroo_ml_ops_api_client.models import (
            OneshotRequest,
            OneshotRequestJson,
        )

        oneshot = OneshotRequest(
            OneshotRequestJson.from_dict(json_args),
            self.id(),
            self.workspace_id(),
            timeout=timeout,
            name=name,
            debug=debug,
        )
        ret = sync_detailed(client=self.client.mlops(), body=oneshot)

        if ret.status_code < 200 or ret.status_code >= 300:
            err = ret.content.decode("utf-8")
            raise OrchestrationDeployOneshotFailed(err)

        return Task(self.client, json.loads(ret.content))

    def run_scheduled(
        self,
        name: str,
        schedule: str,
        json_args: Dict[Any, Any] = {},
        timeout: Optional[int] = None,
        debug: Optional[bool] = False,
    ):
        """Runs this Orchestration on a cron schedule.

        :param: name str A descriptive identifier for this run.
        :param: schedule str A cron-style scheduling string, e.g. "* * * * *" or "*/15 * * * *"
        :param: json_args Dict[Any, Any] A JSON object containing deploy-specific arguments.
        :param: timeout Optional[int] A timeout in seconds. Any single instance of this orchestration that is running for longer than this specified time will be automatically killed. Future runs will still be scheduled.
        :param: debug Optional[bool] Produce extra debugging output about the run
        :return: A metadata object associated with the deploy Task
        """
        from wallaroo.wallaroo_ml_ops_api_client.api.task.cron_job import sync_detailed
        from wallaroo.wallaroo_ml_ops_api_client.models import (
            CronJobBody,
            CronJobBodyJson,
        )

        cronjob = CronJobBody(
            name=name,
            timeout=timeout,
            schedule=schedule,
            orch_id=self.id(),
            json=CronJobBodyJson.from_dict(json_args),
            workspace_id=self.workspace_id(),
            debug=debug,
        )
        ret = sync_detailed(client=self.client.mlops(), body=cronjob)

        if ret.status_code < 200 or ret.status_code >= 300:
            err = ret.content.decode("utf-8")
            raise OrchestrationDeployOneshotFailed(err)

        return Task(self.client, json.loads(ret.content))

    def run_continuously(
        self,
        name: str,
        json_args: Dict[Any, Any] = {},
        debug: Optional[bool] = False,
        # service_name: Optional[str] = None,
        # service_port: Optional[int] = None,
        # service_protocol: Optional[str] = None,
    ):
        """Runs this Orchestration continuously.
        :param: name str A descriptive identifier for this run.
        :param: json_args Dict[Any, Any] A JSON object containing deploy-specific arguments.
        :param: debug Optional[bool] Produce extra debugging output about the run
        :return: A metadata object associated with the deploy Task
        """
        # :param: service_name str A descriptive identifier for the service.
        # :param: service_port int A port number to expose for the service.
        # :param: service_protocol str Protocols to use for the service.
        from wallaroo.wallaroo_ml_ops_api_client.api.task.network_service import (
            sync_detailed,
        )
        from wallaroo.wallaroo_ml_ops_api_client.models import (
            NetworkServiceRequest,
            NetworkServiceRequestJson,
        )

        network_service = NetworkServiceRequest(
            name=name,
            # service_name=service_name,
            # service_port=service_port,
            # service_protocol=service_protocol,
            orch_id=self.id(),
            json=NetworkServiceRequestJson.from_dict(json_args),
            workspace_id=self.workspace_id(),
            debug=debug,
        )
        ret = sync_detailed(client=self.client.mlops(), body=network_service)

        if ret.status_code < 200 or ret.status_code >= 300:
            err = ret.content.decode("utf-8")
            raise OrchestrationDeployOneshotFailed(err)

        return Task(self.client, json.loads(ret.content))

    @rehydrate("_id")
    def id(self):
        return self._id

    @rehydrate("_name")
    def name(self):
        return self._name

    @rehydrate("_file_name")
    def file_name(self):
        return self._file_name

    @rehydrate("_sha")
    def sha(self):
        return self._sha

    @rehydrate("_status")
    def status(self):
        self._rehydrate()
        return self._status

    @rehydrate("_created_at")
    def created_at(self):
        return self._created_at

    @rehydrate("_updated_at")
    def updated_at(self):
        return self._updated_at

    @rehydrate("_workspace_id")
    def workspace_id(self):
        return self._workspace_id

    @rehydrate("_task_id")
    def task(self):
        return Task(self.client, {"id": self._task_id})

    def list_tasks(self):
        from .wallaroo_ml_ops_api_client.api.task.task_list import (
            ListTasksRequest,
            sync,
        )

        req = ListTasksRequest(
            orch_id=self.id(), workspace_id=self.client.get_current_workspace().id()
        )
        ret = sync(client=self.client.mlops(), body=req)

        if ret is None:
            # TODO: Better error
            raise Exception("Failed to find tasks for this orchestration.")

        return TaskList([Task(self.client, task.to_dict()) for task in ret])

    def _repr_html_(self) -> str:
        fmt = self.client._time_format
        self._rehydrate()

        created_at = (
            self._created_at
            if isinstance(self._created_at, DehydratedValue)
            else self._created_at.strftime(fmt)
        )

        updated_at = (
            self._updated_at
            if isinstance(self._updated_at, DehydratedValue)
            else self._updated_at.strftime(fmt)
        )
        workspace_name = Workspace(self.client, {"id": self._workspace_id}).name()
        return f"""
        <table>
          <tr>
            <th>Field</th>
            <th>Value</th>
          </tr>
          <tr>
            <td>ID</td><td>{self.id()}</td>
          </tr>
          <tr>
            <td>Name</td><td>{self._name}</td>
          </tr>
          <tr>
            <td>File Name</td><td>{self._file_name}</td>
          </tr>
          <tr>
            <td>SHA</td><td>{self._sha}</td>
          </tr>
          <tr>
            <td>Status</td><td>{self._status}</td>
          </tr>
          <tr>
            <td>Created At</td><td>{created_at}</td>
          </tr>
          <tr>
            <td>Updated At</td><td>{updated_at}</td>
          </tr>
          <tr>
            <td>Workspace ID</td><td>{self._workspace_id}</td>
          </tr>
          <tr>
            <td>Workspace Name</td><td>{workspace_name}</td>
          </tr>
        </table>
        """


class OrchestrationList(List[Orchestration]):
    """Wraps a list of orchestrations for display in a display-aware environment like Jupyter."""

    def _repr_html_(self) -> str:
        def row(orchestration: Orchestration):
            fmt = orchestration.client._time_format
            orchestration._rehydrate()
            sha: str = orchestration.sha()
            sha_first_6 = sha[0:6]
            sha_last_6 = sha[-6::]

            created_at = (
                orchestration._created_at
                if isinstance(orchestration._created_at, DehydratedValue)
                else orchestration._created_at.strftime(fmt)
            )

            updated_at = (
                orchestration._updated_at
                if isinstance(orchestration._updated_at, DehydratedValue)
                else orchestration._updated_at.strftime(fmt)
            )

            workspace_name = Workspace(
                orchestration.client, {"id": orchestration.workspace_id()}
            ).name()
            return (
                "<tr>"
                + f"<td>{orchestration.id()}</td>"
                + f"<td>{orchestration._name}</td>"
                + f"<td>{orchestration._status}</td>"
                + f"<td>{orchestration._file_name}</td>"
                + f"<td>{sha_first_6}...{sha_last_6}</td>"
                + f"<td>{created_at}</td>"
                + f"<td>{updated_at}</td>"
                + f"<td>{orchestration._workspace_id}</td>"
                + f"<td>{workspace_name}</td>"
                + "</tr>"
            )

        fields = [
            "id",
            "name",
            "status",
            "filename",
            "sha",
            "created at",
            "updated at",
            "workspace id",
            "workspace name",
        ]

        if self == []:
            return "(no orchestrations)"
        else:
            return (
                "<table>"
                + "<tr><th>"
                + "</th><th>".join(fields)
                + "</th></tr>"
                + ("".join([row(p) for p in self]))
                + "</table>"
            )


class OrchestrationUploadFailed(Exception):
    """Raised when uploading an Orchestration fails due to a backend issue."""

    def __init__(self, e):
        super().__init__("Orchestration upload failed: {}".format(e))


class OrchestrationMissingFile(Exception):
    """Raised when uploading an Orchestration without providing a file-like object."""

    def __init__(self):
        super().__init__(
            "Orchestration Upload requires either bytes or path to an Orchestration file."
        )


class OrchestrationDeployOneshotFailed(Exception):
    """Raised when deploying an Orchestration fails due to a backend issue."""

    def __init__(self, e):
        super().__init__("Orchestration deploy failed: {}".format(e))
