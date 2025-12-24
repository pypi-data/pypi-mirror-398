from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from dateutil import parser as dateparse

from .object import (
    DehydratedValue,
    Object,
    RequiredAttributeMissing,
    value_if_present,
)

if TYPE_CHECKING:
    # Imports that happen below in methods to fix circular import dependency
    # issues need to also be specified here to satisfy mypy type checking.
    from .client import Client


class TaskRun(Object):
    def __init__(self, client: "Client", data: Dict[str, Any]) -> None:
        self.client = client
        self._task = data["task"]

        super().__init__(
            gql_client=client._gql_client,
            data=data,
        )

    def _fill(self, data: Dict[str, Any]) -> None:
        # This is only set on initialization, so we shouldn't check for it in the response.
        # self._task = data["task"]

        for required_attribute in ["run_id"]:
            if required_attribute not in data:
                raise RequiredAttributeMissing(
                    self.__class__.__name__, required_attribute
                )
        # Required
        self._pod_id = data["run_id"]
        # Optional
        self._status = value_if_present(data, "status")

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
        from .wallaroo_ml_ops_api_client.api.task.get_run_details import (
            sync,
        )
        from .wallaroo_ml_ops_api_client.models.get_run_details_request import (
            GetRunDetailsRequest,
        )
        from .wallaroo_ml_ops_api_client.models.get_run_details_response_200 import (
            GetRunDetailsResponse200,
        )

        req = GetRunDetailsRequest(task=self._task, pod_id=self._pod_id)

        ret = sync(client=self.client.mlops(), body=req)

        if not isinstance(ret, GetRunDetailsResponse200):
            # TODO: Better error
            raise Exception(f"Failed to find Task Run for pod {self._pod_id}")

        return ret.to_dict()

    def logs(self, limit: Optional[int] = None) -> "TaskRunLogs":
        """Returns the application logs for the given Task Run.
        These may be `print` or Exception logs running your Orchestration.

        Note: The default retention policy for Orchestration logs is 30 days.

        :param: limit int Limits the number of lines of logs returned. Starts from the most recent logs.
        :return: A List of str. Each str represents a newline-separated entry from the Task's log.
        :
        """
        from .wallaroo_ml_ops_api_client.api.task.get_logs_for_run import (
            sync,
        )
        from .wallaroo_ml_ops_api_client.models.get_logs_for_run_request import (
            GetLogsForRunRequest,
        )
        from .wallaroo_ml_ops_api_client.models.get_logs_for_run_response_200 import (
            GetLogsForRunResponse200,
        )

        req = GetLogsForRunRequest(self._pod_id, limit)

        ret = sync(client=self.client.mlops(), body=req)

        if not isinstance(ret, GetLogsForRunResponse200):
            # TODO: Better error
            raise Exception("Failed to find logs for this task run.")

        return TaskRunLogs(ret.logs)

    def _repr_html_(self):
        fmt = self.client._time_format
        self._rehydrate()
        return f"""
            <table>
              <tr><th>Field</th><th>Value</th></tr>
              <tr><td>Task</td><td>{self._task}</td></tr>
              <tr><td>Pod ID</td><td>{self._pod_id}</td></tr>
              <tr><td>Status</td><td>{self._status}</td></tr>
              <tr><td>Created At</td><td>{self._created_at.strftime(fmt)}</td></tr>
              <tr><td>Updated At</td><td>{self._updated_at.strftime(fmt)}</td></tr>
            </table>
            """


class TaskRunList(List[TaskRun]):
    def _repr_html_(self) -> str:
        def task_run_row(task_run: TaskRun) -> str:
            fmt: str = "%Y-%d-%b %H:%M:%S"  # TODO obtain from top client
            created_at = (
                task_run._created_at.strftime(fmt)
                if isinstance(task_run._created_at, datetime)
                else "unknown"
            )
            updated_at = (
                task_run._updated_at.strftime(fmt)
                if isinstance(task_run._updated_at, datetime)
                else "unknown"
            )
            return f"""
            <tr>
              <td>{task_run._task}</td>
              <td>{task_run._pod_id}</td>
              <td>{task_run._status}</td>
              <td>{created_at}</td>
              <td>{updated_at}</td>
            </tr>
            """

        fields = [
            "task id",
            "pod id",
            "status",
            "created at",
            "updated at",
        ]

        if self == []:
            return "(no task runs)"
        else:
            return (
                "<table>"
                + "<tr><th>"
                + "</th><th>".join(fields)
                + "</th></tr>"
                + ("".join([task_run_row(p) for p in self]))
                + "</table>"
            )


class TaskRunLogs(List[str]):
    """This is a list of logs associated with a Task run."""

    def _repr_html_(self):
        if len(self) == 0:
            return "(no logs yet)"

        def log_row(log: str):
            split = log.split(" ")
            time = dateparse.isoparse(split[0]).strftime("%Y-%d-%b %H:%M:%S")
            _channel = split[1]
            arr = split[2:]

            # [1:] to remove the prepended F.
            return time + " ".join(arr)[1:]

        logs = "\n".join([log_row(log) for log in self])
        return f"<pre><code>{logs}</code></pre>"
