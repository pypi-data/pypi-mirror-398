import datetime
import sys
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union, cast

from dateutil import parser as dateparse

from wallaroo import queries
from wallaroo.pipeline_publish import PipelinePublish
from wallaroo.utils import _unwrap

from .deployment import Deployment
from .deployment_config import DeploymentConfig, DeploymentConfigBuilder
from .engine_config import Acceleration, Architecture, InvalidAccelerationError
from .model_config import ModelConfig
from .object import (
    DehydratedValue,
    EntityNotFoundError,
    Object,
    RequiredAttributeMissing,
    gql,
    rehydrate,
    value_if_present,
)
from .pipeline_config import Step, Steps
from .wallaroo_ml_ops_api_client.api.pipelines import pipelines_deploy
from .wallaroo_ml_ops_api_client.models import (
    pipelines_deploy_body,
)
from .wallaroo_ml_ops_api_client.types import UNSET

if TYPE_CHECKING:
    # Imports that happen below in methods to fix circular import dependency
    # issues need to also be specified here to satisfy mypy type checking.
    from .client import Client
    from .pipeline import Pipeline


class PipelineVersion(Object):
    """
    A specific version of a Pipeline. This usually reflects a change to the Pipeline Definition.
    """

    def __init__(self, client: "Client", data: Dict[str, Any]) -> None:
        self.client = client
        assert client is not None
        super().__init__(gql_client=client._gql_client, data=data)

    def _fill(self, data: Dict[str, Any]) -> None:
        from .pipeline import Pipeline  # avoids circular imports

        for required_attribute in ["id"]:
            if required_attribute not in data:
                raise RequiredAttributeMissing(
                    self.__class__.__name__, required_attribute
                )
        self._id = data["id"]

        self._create_time = (
            dateparse.isoparse(data["created_at"])
            if "created_at" in data
            else DehydratedValue()
        )
        self._last_update_time = (
            dateparse.isoparse(data["updated_at"])
            if "updated_at" in data
            else DehydratedValue()
        )
        self._name = value_if_present(data, "version")
        self._definition = value_if_present(data, "definition")
        self._pipeline = (
            Pipeline(client=self.client, data=data["pipeline"])
            if "pipeline" in data
            else DehydratedValue()
        )
        self._deployments = (
            [
                Deployment(
                    client=self.client,
                    data=elem["deployment"],
                )
                for elem in data["deployment_pipeline_versions"]
            ]
            if "deployment_pipeline_versions" in data
            else DehydratedValue()
        )
        self._model_configs = (
            [
                ModelConfig(
                    client=self.client,
                    data=elem["model_config"],
                )
                for elem in data["deployment_model_configs"]
            ]
            if "deployment_model_configs" in data
            else []
        )
        self._publishes = [
            PipelinePublish(client=_unwrap(self.client), **data)
            for data in data.get("pipeline_publishes", [])
        ]
        # Special handling for model configs
        if (
            len(self._model_configs) == 0
            and not isinstance(self._definition, DehydratedValue)
            and self._definition.get("steps") is not None
        ):
            for step in self._definition["steps"]:
                if "ModelInference" in step:
                    name = step["ModelInference"]["models"][0]["name"]
                    version = step["ModelInference"]["models"][0]["version"]
                    try:
                        model = _unwrap(self.client).model_version_by_name(
                            model_class=name, model_name=version
                        )
                    except EntityNotFoundError:
                        model = None
                        pass
                    mc = model.config() if model is not None else "ModelVersionNotFound"
                    self._model_configs.append(mc)  # type: ignore

    def _fetch_attributes(self) -> Dict[str, Any]:
        return self._gql_client.execute(
            gql.gql(queries.named("PipelineVariantById")),
            variable_values={
                "variant_id": self._id,
            },
        )["pipeline_version_by_pk"]

    def id(self) -> int:
        return self._id

    @rehydrate("_create_time")
    def create_time(self) -> datetime.datetime:
        return cast(datetime.datetime, self._create_time)

    @rehydrate("_last_update_time")
    def last_update_time(self) -> datetime.datetime:
        return cast(datetime.datetime, self._last_update_time)

    @rehydrate("_name")
    def name(self) -> str:
        return cast(str, self._name)

    @rehydrate("_definition")
    def definition(self) -> Dict[str, Any]:
        return cast(Dict[str, Any], self._definition)

    @rehydrate("_pipeline")
    def pipeline(self) -> "Pipeline":
        from .pipeline import Pipeline

        return cast(Pipeline, self._pipeline)

    @rehydrate("_deployments")
    def deployments(self) -> List[Deployment]:
        return cast(List[Deployment], self._deployments)

    @rehydrate("_model_configs")
    def model_configs(self) -> List[ModelConfig]:
        return cast(List[ModelConfig], self._model_configs)

    @rehydrate("_publishes")
    def publishes(self) -> List[PipelinePublish]:
        return cast(List[PipelinePublish], self._publishes)

    def deploy(
        self,
        deployment_name: str,
        model_configs: List[ModelConfig],
        config: Optional[DeploymentConfig] = None,
        wait_for_status: Optional[bool] = True,
    ) -> Union[None, Deployment]:
        """Deploys this PipelineVersion.

        :param deployment_name: Name of the new Deployment. Must be unique
            across all deployments.
        :param model_configs: List of the configured models to
        use. These must be the same ModelConfigs used when creating the
            Pipeline.
        :param config: Deployment configuration to use.
        :param wait_for_status: If set to False, will not wait for deployment status.
            If set to True, will wait for deployment status to be running or encountered an error.
            Default is True.
        :return: A Deployment object for the resulting deployment.
        :rtype: Deployment
        """
        workspace_id = (
            None if self.client is None else self.client.get_current_workspace().id()
        )
        if config is None:
            config = DeploymentConfigBuilder(workspace_id=workspace_id).build()
        else:
            config._guarantee_workspace_id(workspace_id=workspace_id)

        assert self.client is not None

        config = PipelineVersion._validate_deployment_config(config, model_configs)

        body = pipelines_deploy_body.PipelinesDeployBody(
            pipeline_version_pk_id=self.id(),
            deploy_id=deployment_name,
            engine_config=config,
            model_configs=UNSET,
            model_ids=UNSET,
            models=UNSET,
            pipeline_id=UNSET,
            pipeline_version=UNSET,
        )

        data = pipelines_deploy.sync(client=self.client.mlops(), body=body)

        if data is None:
            raise Exception("Failed to deploy.")

        deployment = Deployment(client=self.client, data=data.to_dict())

        deployment._rehydrate()

        # Increase timeout for each MLFlow image, up to a limit. Based on very limited testing,
        # multiple MLFlow images do require more time than a single image due to some network
        # saturation.
        timeout_multiplier = 1
        for mc in model_configs:
            if mc.runtime() == "mlflow" and timeout_multiplier < 3:
                timeout_multiplier += 1

        if wait_for_status:
            return deployment.wait_for_running(self.client.timeout * timeout_multiplier)
        else:
            sys.stdout.write(
                f"Deployment initiated for {deployment_name}. Please check pipeline status.\n"
            )

        return deployment

    @staticmethod
    def _validate_deployment_config(
        config: DeploymentConfig, model_configs: List[ModelConfig]
    ) -> DeploymentConfig:
        arch = config["engine"].get("arch")
        accel = config["engine"].get("accel")

        # default deployment architecture and acceleration to the first explicit setting in models
        if arch is None and accel is None:
            for mc in model_configs:
                mv = mc.model_version()
                model_arch = mv.arch()
                model_accel = mv.accel()
                if model_arch is not None or model_accel is not None:
                    config["engine"]["arch"] = arch = model_arch or str(
                        Architecture.default()
                    )
                    config["engine"]["accel"] = accel = model_accel or str(
                        Acceleration.default()
                    )
                    DeploymentConfigBuilder._adjust_gpu_resources(
                        config["engine"],
                        DeploymentConfigBuilder.convert_acceleration(
                            model_accel or str(Acceleration.default())
                        ),
                        Acceleration.default(),
                    )

                    break

        if arch is None:
            config["engine"]["arch"] = arch = str(Architecture.default())

        if accel is None:
            config["engine"]["accel"] = str(Acceleration.default())
        else:
            arch = Architecture(arch)
            accel = DeploymentConfigBuilder.convert_acceleration(accel)
            if not accel.is_applicable(arch):
                raise InvalidAccelerationError()

        if "engineAux" in config and "images" in config["engineAux"]:
            mvs = {
                mv.uid(): {"arch": mv.arch(), "accel": mv.accel()}
                for mv in [mc.model_version() for mc in model_configs]
            }
            for id, image in config["engineAux"]["images"].items():
                arch = image.get("arch")
                if arch is None:
                    image["arch"] = arch = mvs.get(id, {}).get("arch") or str(
                        Architecture.default()
                    )

                accel = image.get("accel")
                if accel is None:
                    image["accel"] = accel = mvs.get(id, {}).get("accel") or str(
                        Acceleration.default()
                    )
                    DeploymentConfigBuilder._adjust_gpu_resources(
                        image,
                        DeploymentConfigBuilder.convert_acceleration(image["accel"]),
                        Acceleration.default(),
                    )

                arch = Architecture(arch)
                accel = DeploymentConfigBuilder.convert_acceleration(accel)
                if not accel.is_applicable(arch):
                    raise InvalidAccelerationError()

        return config

    def _repr_html_(self) -> str:
        fmt = _unwrap(self.client)._time_format
        pipeline = self.pipeline()
        deployments = self.deployments()
        deployed = False if not deployments else deployments[0].deployed()
        steps = Steps(
            [Step.from_json(step) for step in self.definition().get("steps", [])]
        )
        tags = ", ".join([tag.tag() for tag in pipeline.tags()])
        return f"""
        <table>
          <tr><td>name</td><td>{pipeline.name()}</td></tr>
          <tr><td>version</td><td>{self.name()}</td></tr>
          <tr><td>creation_time</td><td>{self.create_time().strftime(fmt)}</td></tr>
          <tr><td>last_updated_time</td><td>{self.last_update_time().strftime(fmt)}</td></tr>
          <tr><td>deployed</td><td>{deployed}</td></tr>
          <tr><td>tags</td><td>{tags}</td></tr>
          <tr><td>steps</td><td>{steps._repr_html_()}</td></tr>
        </table>
        """

    def publish(
        self,
        deployment_config: Optional[DeploymentConfig] = None,
        replaces: Optional[List[Union[int, PipelinePublish]]] = None,
    ):
        """Publish a pipeline version."""
        from .wallaroo_ml_ops_api_client.api.pipelines.publish_pipeline import (
            PublishPipelineBody,
            sync_detailed as sync,
        )

        assert self.client is not None

        # Ensure we get all the model configs in special case
        self._rehydrate()

        model_configs = self.model_configs()
        if deployment_config is not None:
            deployment_config = PipelineVersion._validate_deployment_config(
                deployment_config, model_configs
            )

        engine = (
            deployment_config._deploy_config_to_engine_config()
            if deployment_config is not None
            else None
        )

        replaces_int: List[int] = []

        if replaces is not None:
            replaces_int = [
                pub.id if isinstance(pub, PipelinePublish) else pub for pub in replaces
            ]

        res = sync(
            client=self.client.mlops(),
            body=PublishPipelineBody(
                model_config_ids=[mc.id() for mc in model_configs],
                pipeline_version_id=self.id(),
                engine_config=engine,
                replaces=replaces_int,
            ),
        )
        if res.status_code != 202 or res.parsed is None:
            raise Exception("Failed to publish pipeline.", res.content)
        return PipelinePublish(
            client=self.client, **res.parsed.to_dict()
        )._wait_for_status(
            include_replace_bundles=(replaces is not None and len(replaces) > 0)
        )


class PipelineVersionList(List[PipelineVersion]):
    """Wraps a list of pipeline versions for display in a display-aware environment like Jupyter."""

    def _repr_html_(self) -> str:
        def row(pipeline_version):
            # TODO: we shouldn't be accessing a protected member. No side effects now, so deal with it later.
            fmt = pipeline_version.client._time_format
            pipeline = pipeline_version.pipeline()
            tags = ", ".join([tag.tag() for tag in pipeline.tags()])
            deployments = pipeline_version.deployments()
            deployed = "(unknown)" if not deployments else deployments[0].deployed()
            model_configs = pipeline_version.model_configs()
            steps = ", ".join([mc.model_version().name() for mc in model_configs])
            return (
                "<tr>"
                + f"<td>{pipeline.name()}</td>"
                + f"<td>{pipeline_version.name()}</td>"
                + f"<td>{pipeline_version.create_time().strftime(fmt)}</td>"
                + f"<td>{pipeline_version.last_update_time().strftime(fmt)}</td>"
                + f"<td>{deployed}</td>"
                + f"<td>{pipeline.workspace().id()}</td>"
                + f"<td>{pipeline.workspace().name()}</td>"
                + f"<td>{tags}</td>"
                + f"<td>{steps}</td>"
                + "</tr>"
            )

        fields = [
            "name",
            "version",
            "creation_time",
            "last_updated_time",
            "deployed",
            "workspace_id",
            "workspace_name",
            "tags",
            "steps",
        ]

        if not self:
            return "(no pipelines)"
        else:
            return (
                "<table>"
                + "<tr><th>"
                + "</th><th>".join(fields)
                + "</th></tr>"
                + ("".join([row(p) for p in self]))
                + "</table>"
            )
