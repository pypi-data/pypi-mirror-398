import datetime
import json
import time
from http import HTTPStatus
from math import ceil
from typing import TYPE_CHECKING, Any, Dict, List, cast

from dateutil import parser as dateparse

from wallaroo.utils import _unwrap

from .edge import Edge, EdgeList
from .wallaroo_ml_ops_api_client.api.pipelines.add_edge_to_publish import (
    AddEdgeToPublishBody,
    sync_detailed as sync,
)
from .wallaroo_ml_ops_api_client.api.pipelines.list_edges_by_publish_id import (
    ListEdgesByPublishIdBody,
    sync_detailed as sync_list_edges,
)
from .wallaroo_ml_ops_api_client.models import PipelinePublishStatus
from .wallaroo_ml_ops_api_client.models.publish_pipeline_response_202 import (
    PublishPipelineResponse202,
)
from .wallaroo_ml_ops_api_client.types import UNSET

if TYPE_CHECKING:
    # Imports that happen below in methods to fix circular import dependency
    # issues need to also be specified here to satisfy mypy type checking.
    from .client import Client


class PipelinePublish(PublishPipelineResponse202):
    # Chart URL isn't currently returned by all routes.
    def __init__(self, client: "Client", chart_url=None, **data):
        data.setdefault("docker_run_variables", {})
        data.setdefault("replaces", [])
        data.setdefault("pipeline_name", "")
        data.setdefault("created_on_version", "2024.1.0")
        super().__init__(**data)
        self.client = client
        self.created_at = dateparse.isoparse(cast(str, data.get("created_at")))
        self.updated_at = dateparse.isoparse(cast(str, data.get("updated_at")))
        if isinstance(self.created_by, str):
            self.created_by_email = client.get_email_by_id(self.created_by)

    def _wait_for_status(self, include_replace_bundles=False):
        from .wallaroo_ml_ops_api_client.api.pipelines.get_publish_status import (
            GetPublishStatusBody,
            sync_detailed,
        )

        timeout_limit = 600  # 600 seconds, or 10 minutes.

        poll_interval = 5
        expire_time = datetime.datetime.now() + datetime.timedelta(
            seconds=timeout_limit
        )
        print(f"Waiting for pipeline publish... It may take up to {timeout_limit} sec.")
        print("Pipeline is publishing.", end="", flush=True)
        while datetime.datetime.now() < expire_time:
            ret = sync_detailed(
                client=self.client.mlops(),
                body=GetPublishStatusBody(
                    id=self.id, include_replace_bundles=include_replace_bundles
                ),
            )
            if ret.parsed is None:
                print(" ERROR!")
                raise Exception(
                    "An error occurred during pipeline publish. Status API returned",
                    ret.content,
                )
            status = ret.parsed.status
            if status == PipelinePublishStatus.PUBLISHED:
                print(" Published.")
                return PipelinePublish(
                    client=self.client, **_unwrap(ret.parsed).to_dict()
                )
            elif status == PipelinePublishStatus.ERROR:
                print(f" ERROR! {ret.parsed.error}")
                raise Exception(
                    f"An error occurred during pipeline publish. {ret.parsed.error}"
                )
            else:
                print(".", end="", flush=True)
                time.sleep(poll_interval)
        else:
            raise Exception(f"Pipeline Publish timed out after {timeout_limit} sec.")

    def _repr_html_(self):
        chart = self._get_helm_value("chart")
        reference = self._get_helm_value("reference")
        version = self._get_helm_value("version")
        helm_install, docker_run, podman_run, edge_bundles, additional_envs = (
            self._generate_commands()
        )
        edges = self.list_edges()
        edges_list = [
            edge.name for edge in edges if edges is not None and edge is not None
        ]

        return f"""
          <table>
              <tr><td>ID</td><td>{self.id}</td></tr>
              <tr><td>Pipeline Name</td><td>{self.pipeline_name}</td></tr>
              <tr><td>Pipeline Version</td><td>{self.pipeline_version_name}</td></tr>
              <tr><td>Status</td><td>{self.status}</td></tr>
              <tr><td>Workspace Id</td><td>{self.workspace_id}</td></tr>
              <tr><td>Workspace Name</td><td>{self.workspace_name}</td></tr>
              <tr><td>Edges</td><td>{'<br/>'.join(edges_list)}</td></tr>
              <tr><td>Engine URL</td><td>{PipelinePublish._null_safe_a_tag(self.engine_url)}</td></tr>
              <tr><td>Pipeline URL</td><td>{PipelinePublish._null_safe_a_tag(self.pipeline_url)}</td></tr>
              <tr><td>Helm Chart URL</td><td>oci://{PipelinePublish._null_safe_a_tag(chart)}</td></tr>
              <tr><td>Helm Chart Reference</td><td>{reference}</td></tr>
              <tr><td>Helm Chart Version</td><td>{version}</td></tr>
              <tr><td>Engine Config</td><td>{self.engine_config}</td></tr>
              <tr><td>User Images</td><td>{self.user_images}</td></tr>
              <tr><td>Created By</td><td>{self.created_by_email}</td></tr>
              <tr><td>Created At</td><td>{self.created_at}</td></tr>
              <tr><td>Updated At</td><td>{self.updated_at}</td></tr>
              <tr><td>Replaces</td><td>{'<br/>'.join(['Publish %s, Pipeline "%s", Version %s' % (r.get('id'), r.get('pipeline_name'), r.get('pipeline_version_name')) for r in self.replaces])}</td></tr>
              <tr>
                  <td>Docker Run Command</td>
                  <td>
                      <table>{docker_run}</table>
                      <br />
                      <i>
                          Note: Please set the {additional_envs}<code>EDGE_PORT</code>, <code>OCI_USERNAME</code>, and <code>OCI_PASSWORD</code> environment variables.
                      </i>
                  </td>
              </tr>
              <tr>
                  <td>Podman Run Command</td>
                  <td>
                      <table>{podman_run}</table>
                      <br />
                      <i>
                          Note: Please set the {additional_envs}<code>EDGE_PORT</code>, <code>OCI_USERNAME</code>, and <code>OCI_PASSWORD</code> environment variables.
                      </i>
                  </td>
              </tr>
              <tr>
                  <td>Helm Install Command</td>
                  <td>
                      <table>{helm_install}</table>
                      <br />
                      <i>
                          Note: Please set the <code>HELM_INSTALL_NAME</code>, <code>HELM_INSTALL_NAMESPACE</code>,
                          <code>OCI_USERNAME</code>, and <code>OCI_PASSWORD</code> environment variables.
                      </i>
                  </td>
              </tr>
              {edge_bundles}
          </table>
        """

    def add_edge(
        self,
        name: str,
        tags: List[str] = [],
    ) -> "PipelinePublish":
        """Add new edge to a published pipeline."""

        assert self.client is not None

        res = sync(
            client=self.client.mlops(),
            body=AddEdgeToPublishBody(
                name=name,
                pipeline_publish_id=self.id,
                tags=tags,
            ),
        )
        if res.status_code != HTTPStatus.CREATED or res.parsed is None:
            raise Exception("Failed to add edge to published pipeline.", res.content)
        return PipelinePublish(client=self.client, **res.parsed.to_dict())

    def remove_edge(
        self,
        name: str,
    ):
        """Remove an edge to a published pipeline.

        :param str name: The name of the edge that will be removed. This is not limited to this pipeline.
        """
        self.client.remove_edge(name)

    def list_edges(self) -> List[Edge]:
        """List all edges in a published pipeline."""
        assert self.client is not None

        res = sync_list_edges(
            client=self.client.mlops(),
            body=ListEdgesByPublishIdBody(
                publish_id=self.id,
            ),
        )
        if res.status_code != HTTPStatus.OK:
            raise Exception("Failed to list edges in published pipeline.", res.content)

        json_ret = json.loads(res.content)

        # Generating additional properties for each edge to display in the HTML table
        helm_install, docker_run, podman_run, edge_bundles, additional_envs = (
            self._generate_commands()
        )

        additional_properties = {
            "pipeline_name": self.pipeline_name,
            "pipeline_version_name": self.pipeline_version_name,
            "workspace_name": self.workspace_name,
            "workspace_id": self.workspace_id,
            "helm_install": helm_install,
            "docker_run": docker_run,
            "podman_run": podman_run,
            "additional_envs": additional_envs,
            "edge_bundles": edge_bundles,
        }

        returned_edges: List[Dict[str, Any]] = [
            {**pub, **additional_properties} for pub in json_ret["edges"]
        ]

        return EdgeList([Edge.from_dict(edge_dict) for edge_dict in returned_edges])

    def _get_helm_value(self, key):
        if self.helm is None or self.helm is UNSET:
            return None
        return self.helm.get(key)

    def _null_safe_a_tag(var):
        return f"<a href='https://{var}'>{var}</a>" if var is not None else None

    def _helm_values(helm_values_dict):
        return (
            ""
            if helm_values_dict is None or len(helm_values_dict) == 0
            else (
                " \\\n    --set "
                + " \\\n    --set ".join(
                    [f"{k}={v}" for k, v in helm_values_dict.items()]
                )
            )
        )

    def _helm_install_html(self, action, vals):
        chart = self._get_helm_value("chart")
        version = self._get_helm_value("version")
        return f"""
<pre style="text-align: left">helm {action} $HELM_INSTALL_NAME \\
    oci://{chart} \\
    --namespace $HELM_INSTALL_NAMESPACE \\
    --version {version} \\
    --set ociRegistry.username=$OCI_USERNAME \\
    --set ociRegistry.password=$OCI_PASSWORD{PipelinePublish._helm_values(vals)}</pre>"""

    def _docker_vars(variables):
        return (
            ""
            if len(variables) == 0
            else (
                " \\\n    -e "
                + "\\\n    -e ".join([f"{k}={v}" for k, v in variables.items()])
            )
        )

    def _docker_run_html(
        self, with_persistent_volume, vars, cpus, memory, gpu, config_cpus=None
    ):
        return f"""
<pre style="text-align: left">docker run {'-v $PERSISTENT_VOLUME_DIR:/persist ' if with_persistent_volume else ''}\\
    -p $EDGE_PORT:8080 \\
    -e OCI_USERNAME=$OCI_USERNAME \\
    -e OCI_PASSWORD=$OCI_PASSWORD{PipelinePublish._docker_vars(vars)} \\
    {'' if config_cpus is None else '-e CONFIG_CPUS=%s ' % config_cpus}{'' if not gpu else '--gpus all '}--cpus={cpus} --memory={memory} \\
    {self.engine_url}</pre>"""

    def _podman_run_html(
        self, with_persistent_volume, vars, cpus, memory, gpu, config_cpus=None
    ):
        return f"""
<pre style="text-align: left">podman run {'-v $PERSISTENT_VOLUME_DIR:/persist ' if with_persistent_volume else ''}\\
    -p $EDGE_PORT:8080 \\
    -e OCI_USERNAME=$OCI_USERNAME \\
    -e OCI_PASSWORD=$OCI_PASSWORD{PipelinePublish._docker_vars(vars)} \\
    {'' if config_cpus is None else '-e CONFIG_CPUS=%s ' % config_cpus}{'' if not gpu else '--device nvidia.com/gpu=all '}--cpus={cpus} --memory={memory} \\
    {self.engine_url}</pre>"""

    def _generate_commands(self):
        chart = self._get_helm_value("chart")
        helm_values_dict = None if chart is None else self.helm.get("values")
        variables = dict((k, v) for k, v in self.docker_run_variables.items())
        engine_limits = (
            self.engine_config.get("engine", {}).get("resources", {}).get("limits", {})
        )
        sidekick_limits = [
            sidekick.get("resources", {}).get("limits", {})
            for sidekick in self.engine_config.get("engineAux", {})
            .get("images", {})
            .values()
        ]
        engine_cpus = float(engine_limits.get("cpu", 0.0))
        sidekick_cpus = [
            float(sidekick.get("cpu", 0.0)) for sidekick in sidekick_limits
        ]
        total_cpus = sum([engine_cpus] + sidekick_cpus)
        sidekick_memory = [sidekick.get("memory") for sidekick in sidekick_limits]
        total_memory = sum_memory(
            [engine_limits.get("memory", "1Gi")]
            + [val for val in sidekick_memory if val is not None]
        )
        gpu = any(
            [
                self.engine_config.get("engine", {})
                .get("resources", {})
                .get("gpu", False)
            ]
            + [
                sidekick.get("resources", {}).get("gpu", False)
                for sidekick in self.engine_config.get("engineAux", {})
                .get("images", {})
                .values()
            ]
        )
        config_cpus = max(
            1.0,
            ceil(engine_cpus),
        )
        edge_bundles = ""
        additional_envs = ""
        helm_install = ""
        docker_run = ""
        podman_run = ""
        if self.edge_bundles != UNSET and len(self.edge_bundles) > 0:
            docker_run += """<tr><td style="text-align: left"><b>Edge</b></td><td style="text-align: left"><b>Command</b></td></tr>"""
            podman_run += """<tr><td style="text-align: left"><b>Edge</b></td><td style="text-align: left"><b>Command</b></td></tr>"""
            helm_install += """<tr><td style="text-align: left"><b>Edge</b></td><td style="text-align: left"><b>Command</b></td></tr>"""
            additional_envs += "<code>PERSISTENT_VOLUME_DIR</code>, "
            for edge, bundle in self.edge_bundles.items():
                variables["EDGE_BUNDLE"] = bundle
                docker_run += f"""<tr><td>{edge}</td><td>{self._docker_run_html(True, variables, total_cpus, total_memory, gpu)}</td></tr>"""
                podman_run += f"""<tr><td>{edge}</td><td>{self._podman_run_html(True, variables, total_cpus, total_memory, gpu)}</td></tr>"""
                helm_values_dict["edgeBundle"] = bundle
                helm_install += f"""<tr><td>{edge}</td><td>{self._helm_install_html('upgrade', helm_values_dict)}</td></tr>"""
        else:
            if "EDGE_BUNDLE" in variables:
                additional_envs += "<code>PERSISTENT_VOLUME_DIR</code>, "
            helm_install += f"""<tr><td>{self._helm_install_html('install --atomic', helm_values_dict)}</td></tr>"""
            docker_run += f"""<tr><td>{self._docker_run_html('EDGE_BUNDLE' in variables, variables, total_cpus, total_memory, gpu, config_cpus)}</td></tr>"""
            podman_run += f"""<tr><td>{self._podman_run_html('EDGE_BUNDLE' in variables, variables, total_cpus, total_memory, gpu, config_cpus)}</td></tr>"""
        return helm_install, docker_run, podman_run, edge_bundles, additional_envs


class PipelinePublishList(List[PipelinePublish]):
    """Wraps a list of published pipelines for display in a display-aware environment like Jupyter."""

    def _repr_html_(self) -> str:
        def row(publish: PipelinePublish):
            fmt = publish.client._time_format

            created_at = publish.created_at.strftime(fmt)
            updated_at = publish.updated_at.strftime(fmt)
            # Get the list of edges for the publish
            edges = publish.list_edges()
            edges_list = (
                [edge.name for edge in edges if edge is not None]
                if edges is not None
                else []
            )

            def null_safe_a_tag(var):
                return f"<a href='https://{var}'>{var}</a>" if var is not None else None

            return (
                "<tr>"
                + f"<td>{publish.id}</td>"
                + f"<td>{publish.pipeline_name}</td>"
                + f"<td>{publish.pipeline_version_name}</td>"
                + f"<td>{publish.workspace_id}</td>"
                + f"<td>{publish.workspace_name}</td>"
                + f"<td>{'<br/>'.join(edges_list)}</td>"
                + f"<td>{null_safe_a_tag(publish.engine_url)}</td>"
                + f"<td>{null_safe_a_tag(publish.pipeline_url)}</td>"
                + f"<td>{publish.created_by_email}</td>"
                + f"<td>{created_at}</td>"
                + f"<td>{updated_at}</td>"
                + "</tr>"
            )

        fields = [
            "id",
            "Pipeline Name",
            "Pipeline Version",
            "Workspace Id",
            "Workspace Name",
            "Edges",
            "Engine URL",
            "Pipeline URL",
            "Created By",
            "Created At",
            "Updated At",
        ]

        if self == []:
            return "(no publishes)"
        else:
            return (
                "<table>"
                + "<tr><th>"
                + "</th><th>".join(fields)
                + "</th></tr>"
                + ("".join([row(p) for p in self]))
                + "</table>"
            )


def sum_memory(values: List[str] = []) -> str:
    if not values:
        return "6m"

    # note: "k" is the correct casing!
    # see https://kubernetes.io/docs/reference/kubernetes-api/common-definitions/quantity/
    si_units = ["k", "M", "G", "T"]
    bin_units = ["Ki", "Mi", "Gi", "Ti"]

    def k8s_to_bytes(value):
        if value.endswith(tuple(bin_units)):
            unit = value[-2:]
            pos = bin_units.index(unit)
            mul = pow(1024, pos + 1)
            return int(value[:-2]) * mul
        if value.endswith(tuple(si_units)):
            unit = value[-1:]
            pos = si_units.index(unit)
            mul = pow(1000, pos + 1)
            return int(value[:-1]) * mul
        return 0

    bytes = sum(map(k8s_to_bytes, values))
    for pos, unit in reversed(list(enumerate(["k", "m", "g", "t"]))):
        mul = pow(1024, pos + 1)
        if bytes % mul == 0:
            return f"{bytes // mul}{unit}"

    return str(bytes)
