import time
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from uuid import UUID

from dateutil import parser as dateparse

from wallaroo.task_run import TaskRun, TaskRunList
from wallaroo.workspace import Workspace

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


class Task(Object):
    def __init__(self, client: "Client", data: Dict[str, Any]) -> None:
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
        self._flavor = value_if_present(data, "flavor")
        self._subject = value_if_present(data, "subject")
        self._status = value_if_present(data, "status")
        self._attempt = value_if_present(data, "attempt")
        self._workspace_id = value_if_present(data, "workspace_id")
        self._calling_user = value_if_present(data, "calling_user")
        self._private = value_if_present(data, "private")
        self._task_type = value_if_present(data, "run_type")
        self._input_data = value_if_present(data, "input_data")
        # serde(flatten) is used, meaning we have to try parsing
        # Union['CronJobExec', 'NetworkServiceExec', 'OneshotExec'] from data ourselves.
        # self._event = value_if_present(data, "event")
        self._all_data = data
        self._killed = value_if_present(data, "killed")
        self._last_runs = (
            TaskRunList(
                [
                    TaskRun(self.client, {"task": self._id, "run_id": d["run_id"]})
                    for d in data["last_runs"]
                ]
            )
            if "last_runs" in data
            else DehydratedValue()
        )

        self._created_at = (
            dateparse.isoparse(data["created_at"])
            if "created_at" in data
            else DehydratedValue()
        )

        self._updated_at = (
            dateparse.isoparse(data["updated_at"])
            if "updated_at" in data
            else DehydratedValue()
        )

    def _fetch_attributes(self) -> Dict[str, Any]:
        from .wallaroo_ml_ops_api_client.api.task.task_get_by_id import sync
        from .wallaroo_ml_ops_api_client.models.get_task_by_id_request import (
            GetTaskByIdRequest,
        )

        req = GetTaskByIdRequest(self._id)

        ret = sync(client=self.client.mlops(), body=req)

        if ret is None:
            # TODO: Better error
            raise Exception(f"Failed to find Task ID {self._id}")

        return ret.to_dict()

    def kill(
        self,
    ):
        """Kill this Task."""
        from .wallaroo_ml_ops_api_client.api.task.kill import sync
        from .wallaroo_ml_ops_api_client.models.kill_request import KillRequest

        ret = sync(client=self.client.mlops(), body=KillRequest(self.id()))

        if ret is None:
            # TODO: Better error
            raise Exception("Failed to send Kill request for this task.")

        return ret.status

    def _pause(
        self,
    ):
        """EXPERIMENTAL: Pause this Task.

        This function takes no input and is called on a Task object that has previously been started
        with the `run_scheduled` method.

        It returns the Task object after the status has changed to `paused`.
        """
        from .wallaroo_ml_ops_api_client.api.task.pause import sync
        from .wallaroo_ml_ops_api_client.models.pause_request import PauseRequest

        ret = sync(client=self.client.mlops(), body=PauseRequest(self.id(), pause=True))

        if ret is None:
            # TODO: Better error
            raise Exception("Failed to send Pause request for this task.")

        return self._wait_for_status(pause=True)

    def _resume(
        self,
    ):
        """EXPERIMENTAL: Resume this Task.

        This function takes no input and is called on a Task object that has previously been Paused.
        It returns the Task object after the state has been successfully changed to `started`
        """
        from .wallaroo_ml_ops_api_client.api.task.pause import sync
        from .wallaroo_ml_ops_api_client.models.pause_request import PauseRequest

        ret = sync(
            client=self.client.mlops(), body=PauseRequest(self.id(), pause=False)
        )

        if ret is None:
            # TODO: Better error
            raise Exception("Failed to send Resume request for this task.")

        return self._wait_for_status(pause=False)

    def _wait_for_status(self, pause=True):
        TIMEOUT_LIMIT = 300  # 300 seconds, or 5 minutes.

        poll_interval = 5
        expire_time = datetime.now() + timedelta(seconds=TIMEOUT_LIMIT)
        pausing_or_resuming = "Pausing" if pause else "Resuming"
        print(
            f"{pausing_or_resuming.title()} task... It may take up to {TIMEOUT_LIMIT} sec."
        )
        print("Task is ", end="", flush=True)
        while datetime.now() < expire_time:
            status = self.status()
            if status is None:
                print("ERROR!")
                raise Exception(
                    f"An error occurred during task {pausing_or_resuming}. Status is None",
                )
            if status.lower() == "paused":
                print("Paused.")
                return self
            if status.lower() == "started":
                print("Resumed.")
                return self
            elif status.lower() == "error":
                print("ERROR!")
                raise Exception(f"An error occurred during task {pausing_or_resuming}.")
            else:
                print(".", end="", flush=True)
                time.sleep(poll_interval)
        else:
            raise Exception(
                f"Task {pausing_or_resuming} timed out after {TIMEOUT_LIMIT} sec."
            )

    @staticmethod
    def list_tasks(
        client: "Client", killed: bool = False, workspace_id: Optional[int] = None
    ) -> "TaskList":
        from .wallaroo_ml_ops_api_client.api.task.task_list import sync
        from .wallaroo_ml_ops_api_client.models.list_tasks_request import (
            ListTasksRequest,
        )

        ret = sync(
            client=client.mlops(),
            body=ListTasksRequest(workspace_id=workspace_id, killed=killed),
        )

        if ret is None:
            raise Exception("Failed to find Tasks in workspace")

        return TaskList([Task(client, r.to_dict()) for r in ret])

    @staticmethod
    def get_task_by_id(client: "Client", task_id: str):
        from .wallaroo_ml_ops_api_client.api.task.task_get_by_id import sync
        from .wallaroo_ml_ops_api_client.models.get_task_by_id_request import (
            GetTaskByIdRequest,
        )

        ret = sync(client=client.mlops(), body=GetTaskByIdRequest(UUID(task_id)))

        if ret is None:
            raise Exception(f"Failed to find Task ID {task_id}")

        return Task(client, ret.to_dict())

    def _descriptive_task_type(self):
        """This is a convenience function to parse the associated Event data into a type the User is familiar with."""
        task_type_mapping = {
            "Oneshot": "Temporary Run",
            "CronJob": "Scheduled Run",
            "NetworkService": "Continuous Run",
        }
        return task_type_mapping.get(self.task_type(), "Custom Image Run")

    def _last_run_status(self):
        try:
            last = self._all_data["last_runs"][-1]["status"]
        except Exception:
            last = "unknown"
        return last

    def _descriptive_schedule(self):
        sched = self._all_data.get("schedule")
        return sched if sched else "-"

    @rehydrate("_id")
    def id(self):
        return self._id

    @rehydrate("_name")
    def name(self):
        return self._name

    @rehydrate("_workspace_id")
    def workspace_id(self):
        return self._workspace_id

    @rehydrate("_input_data")
    def input_data(self):
        return self._input_data

    @rehydrate("_status")
    def status(self):
        self._rehydrate()
        return self._status

    @rehydrate("_task_type")
    def task_type(self):
        return self._task_type

    @rehydrate("_created_at")
    def created_at(self):
        return self._created_at

    @rehydrate("_updated_at")
    def updated_at(self):
        return self._updated_at

    # This is an attribute, but because it can be filtered, we handle it differently.
    # @rehydrate("_last_runs")
    # def last_runs(self):
    #     return self._last_runs

    def last_runs(
        self, limit: Optional[int] = None, status: Optional[str] = None
    ) -> "TaskRunList":
        """Return the runs associated with this task.

        :param: limit int The number of runs to return
        :param: status str Return only runs with the matching status. One of "success", "failure", "running", "all"
        """
        from .wallaroo_ml_ops_api_client.api.task.list_task_runs import sync
        from .wallaroo_ml_ops_api_client.models.list_task_runs_request import (
            ListTaskRunsRequest,
        )
        from .wallaroo_ml_ops_api_client.models.list_task_runs_request_status import (
            ListTaskRunsRequestStatus,
        )

        # Forces a nicer error message if not a valid status
        status = ListTaskRunsRequestStatus(status) if status is not None else None

        req = ListTaskRunsRequest(task_id=self.id(), limit=limit, status=status)

        ret = sync(client=self.client.mlops(), body=req)

        if ret is None:
            raise Exception("No runs found for this Task.")

        return TaskRunList(
            [TaskRun(client=self.client, data=run.to_dict()) for run in ret]
        )

    def _repr_html_(self) -> str:
        fmt = self.client._time_format
        self._rehydrate()
        workspace_name = Workspace(self.client, {"id": self.workspace_id()}).name()
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
            <td>Last Run Status</td><td>{self._last_run_status()}</td>
          </tr>
          <tr>
            <td>Type</td><td>{self._descriptive_task_type()}</td>
          </tr>
          <tr>
            <td>Active</td><td>{not self._killed}</td>
          </tr>
          <tr>
            <td>Schedule</td><td>{self._descriptive_schedule()}</td>
          </tr>
          <tr>
            <td>Created At</td><td>{self.created_at().strftime(fmt)}</td>
          </tr>
          <tr>
            <td>Updated At</td><td>{self.updated_at().strftime(fmt)}</td>
          </tr>
          <tr>
            <td>Workspace ID</td><td>{self.workspace_id()}</td>
          </tr>
          <tr>
            <td>Workspace Name</td><td>{workspace_name}</td>
          </tr>
        </table>
        """


class TaskList(List[Task]):
    """Wraps a list of pipelines for display in a display-aware environment like Jupyter."""

    def _repr_html_(self) -> str:
        def row(task: Task):
            fmt = task.client._time_format
            task._rehydrate()
            workspace_name = Workspace(task.client, {"id": task.workspace_id()}).name()
            return (
                "<tr>"
                + f"<td>{task.id()}</td>"
                + f"<td>{task._name}</td>"
                + f"<td>{task._last_run_status()}</td>"
                + f"<td>{task._descriptive_task_type()}</td>"
                + f"<td>{not task._killed}</td>"
                + f"<td>{task._descriptive_schedule()}</td>"
                + f"<td>{task.created_at().strftime(fmt)}</td>"
                + f"<td>{task.updated_at().strftime(fmt)}</td>"
                + f"<td>{task.workspace_id()}</td>"
                + f"<td>{workspace_name}</td>"
                + "</tr>"
            )

        fields = [
            "id",
            "name",
            "last run status",
            "type",
            "active",
            "schedule",
            "created at",
            "updated at",
            "workspace id",
            "workspace name",
        ]

        if self == []:
            return "(no tasks)"
        else:
            return (
                "<table>"
                + "<tr><th>"
                + "</th><th>".join(fields)
                + "</th></tr>"
                + ("".join([row(p) for p in self]))
                + "</table>"
            )
