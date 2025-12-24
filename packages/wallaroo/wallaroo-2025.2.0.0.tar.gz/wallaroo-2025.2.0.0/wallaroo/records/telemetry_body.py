# This code parses date/times, so please
#
#     pip install python-dateutil
#
# To use this code, make sure you
#
#     import json
#
# and then, to convert JSON from a string, do
#
#     result = wallaroo_api_telemetry_data_v1_from_dict(json.loads(json_string))

from typing import Any, List, TypeVar, Type, cast, Callable
from uuid import UUID
from datetime import datetime
import dateutil.parser


T = TypeVar("T")


def from_int(x: Any) -> int:
    assert isinstance(x, int) and not isinstance(x, bool)
    return x


def to_class(c: Type[T], x: Any) -> dict:
    assert isinstance(x, c)
    return cast(Any, x).to_dict()


def from_str(x: Any) -> str:
    assert isinstance(x, str)
    return x


def from_bool(x: Any) -> bool:
    assert isinstance(x, bool)
    return x


def from_list(f: Callable[[Any], T], x: Any) -> List[T]:
    assert isinstance(x, list)
    return [f(y) for y in x]


def from_datetime(x: Any) -> datetime:
    return dateutil.parser.parse(x)


class ModelConfigElement:
    id: int

    def __init__(self, id: int) -> None:
        self.id = id

    @staticmethod
    def from_dict(obj: Any) -> "ModelConfigElement":
        assert isinstance(obj, dict)
        id = from_int(obj.get("id"))
        return ModelConfigElement(id)

    def to_dict(self) -> dict:
        result: dict = {}
        result["id"] = from_int(self.id)
        return result


class DeploymentModelConfig:
    model_config: ModelConfigElement

    def __init__(self, model_config: ModelConfigElement) -> None:
        self.model_config = model_config

    @staticmethod
    def from_dict(obj: Any) -> "DeploymentModelConfig":
        assert isinstance(obj, dict)
        model_config = ModelConfigElement.from_dict(obj.get("model_config"))
        return DeploymentModelConfig(model_config)

    def to_dict(self) -> dict:
        result: dict = {}
        result["model_config"] = to_class(ModelConfigElement, self.model_config)
        return result


class Deployment:
    deploy_id: str
    deployed: bool
    deployment_model_configs: List[DeploymentModelConfig]
    id: int

    def __init__(
        self,
        deploy_id: str,
        deployed: bool,
        deployment_model_configs: List[DeploymentModelConfig],
        id: int,
    ) -> None:
        self.deploy_id = deploy_id
        self.deployed = deployed
        self.deployment_model_configs = deployment_model_configs
        self.id = id

    @staticmethod
    def from_dict(obj: Any) -> "Deployment":
        assert isinstance(obj, dict)
        deploy_id = from_str(obj.get("deploy_id"))
        deployed = from_bool(obj.get("deployed"))
        deployment_model_configs = from_list(
            DeploymentModelConfig.from_dict, obj.get("deployment_model_configs")
        )
        id = from_int(obj.get("id"))
        return Deployment(deploy_id, deployed, deployment_model_configs, id)

    def to_dict(self) -> dict:
        result: dict = {}
        result["deploy_id"] = from_str(self.deploy_id)
        result["deployed"] = from_bool(self.deployed)
        result["deployment_model_configs"] = from_list(
            lambda x: to_class(DeploymentModelConfig, x), self.deployment_model_configs
        )
        result["id"] = from_int(self.id)
        return result


class WelcomeModel:
    file_name: str
    id: int
    model_id: str
    model_version: UUID
    updated_at: datetime

    def __init__(
        self,
        file_name: str,
        id: int,
        model_id: str,
        model_version: UUID,
        updated_at: datetime,
    ) -> None:
        self.file_name = file_name
        self.id = id
        self.model_id = model_id
        self.model_version = model_version
        self.updated_at = updated_at

    @staticmethod
    def from_dict(obj: Any) -> "WelcomeModel":
        assert isinstance(obj, dict)
        file_name = from_str(obj.get("file_name"))
        id = from_int(obj.get("id"))
        model_id = from_str(obj.get("model_id"))
        model_version = UUID(obj.get("model_version"))
        updated_at = from_datetime(obj.get("updated_at"))
        return WelcomeModel(file_name, id, model_id, model_version, updated_at)

    def to_dict(self) -> dict:
        result: dict = {}
        result["file_name"] = from_str(self.file_name)
        result["id"] = from_int(self.id)
        result["model_id"] = from_str(self.model_id)
        result["model_version"] = str(self.model_version)
        result["updated_at"] = self.updated_at.isoformat()
        return result


class WelcomePipeline:
    id: int
    pipeline_tags: List[Any]

    def __init__(self, id: int, pipeline_tags: List[Any]) -> None:
        self.id = id
        self.pipeline_tags = pipeline_tags

    @staticmethod
    def from_dict(obj: Any) -> "WelcomePipeline":
        assert isinstance(obj, dict)
        id = from_int(obj.get("id"))
        pipeline_tags = from_list(lambda x: x, obj.get("pipeline_tags"))
        return WelcomePipeline(id, pipeline_tags)

    def to_dict(self) -> dict:
        result: dict = {}
        result["id"] = from_int(self.id)
        result["pipeline_tags"] = from_list(lambda x: x, self.pipeline_tags)
        return result


class WorkspaceModel:
    models: List[ModelConfigElement]

    def __init__(self, models: List[ModelConfigElement]) -> None:
        self.models = models

    @staticmethod
    def from_dict(obj: Any) -> "WorkspaceModel":
        assert isinstance(obj, dict)
        models = from_list(ModelConfigElement.from_dict, obj.get("models"))
        return WorkspaceModel(models)

    def to_dict(self) -> dict:
        result: dict = {}
        result["models"] = from_list(
            lambda x: to_class(ModelConfigElement, x), self.models
        )
        return result


class Workspace:
    archived: bool
    created_at: datetime
    created_by: UUID
    id: int
    models: List[WorkspaceModel]
    name: str
    pipelines: List[ModelConfigElement]

    def __init__(
        self,
        archived: bool,
        created_at: datetime,
        created_by: UUID,
        id: int,
        models: List[WorkspaceModel],
        name: str,
        pipelines: List[ModelConfigElement],
    ) -> None:
        self.archived = archived
        self.created_at = created_at
        self.created_by = created_by
        self.id = id
        self.models = models
        self.name = name
        self.pipelines = pipelines

    @staticmethod
    def from_dict(obj: Any) -> "Workspace":
        assert isinstance(obj, dict)
        archived = from_bool(obj.get("archived"))
        created_at = from_datetime(obj.get("created_at"))
        created_by = UUID(obj.get("created_by"))
        id = from_int(obj.get("id"))
        models = from_list(WorkspaceModel.from_dict, obj.get("models"))
        name = from_str(obj.get("name"))
        pipelines = from_list(ModelConfigElement.from_dict, obj.get("pipelines"))
        return Workspace(archived, created_at, created_by, id, models, name, pipelines)

    def to_dict(self) -> dict:
        result: dict = {}
        result["archived"] = from_bool(self.archived)
        result["created_at"] = self.created_at.isoformat()
        result["created_by"] = str(self.created_by)
        result["id"] = from_int(self.id)
        result["models"] = from_list(lambda x: to_class(WorkspaceModel, x), self.models)
        result["name"] = from_str(self.name)
        result["pipelines"] = from_list(
            lambda x: to_class(ModelConfigElement, x), self.pipelines
        )
        return result


class WallarooAPITelemetryDataV1:
    api_key: str
    deployments: List[Deployment]
    models: List[WelcomeModel]
    pipelines: List[WelcomePipeline]
    users: int
    workspaces: List[Workspace]

    def __init__(
        self,
        api_key: str,
        deployments: List[Deployment],
        models: List[WelcomeModel],
        pipelines: List[WelcomePipeline],
        users: int,
        workspaces: List[Workspace],
    ) -> None:
        self.api_key = api_key
        self.deployments = deployments
        self.models = models
        self.pipelines = pipelines
        self.users = users
        self.workspaces = workspaces

    @staticmethod
    def from_dict(obj: Any) -> "WallarooAPITelemetryDataV1":
        assert isinstance(obj, dict)
        api_key = from_str(obj.get("api_key"))
        deployments = from_list(Deployment.from_dict, obj.get("deployments"))
        models = from_list(WelcomeModel.from_dict, obj.get("models"))
        pipelines = from_list(WelcomePipeline.from_dict, obj.get("pipelines"))
        users = from_int(obj.get("users"))
        workspaces = from_list(Workspace.from_dict, obj.get("workspaces"))
        return WallarooAPITelemetryDataV1(
            api_key, deployments, models, pipelines, users, workspaces
        )

    def to_dict(self) -> dict:
        result: dict = {}
        result["api_key"] = from_str(self.api_key)
        result["deployments"] = from_list(
            lambda x: to_class(Deployment, x), self.deployments
        )
        result["models"] = from_list(lambda x: to_class(WelcomeModel, x), self.models)
        result["pipelines"] = from_list(
            lambda x: to_class(WelcomePipeline, x), self.pipelines
        )
        result["users"] = from_int(self.users)
        result["workspaces"] = from_list(
            lambda x: to_class(Workspace, x), self.workspaces
        )
        return result


def wallaroo_api_telemetry_data_v1_from_dict(s: Any) -> WallarooAPITelemetryDataV1:
    return WallarooAPITelemetryDataV1.from_dict(s)


def wallaroo_api_telemetry_data_v1_to_dict(x: WallarooAPITelemetryDataV1) -> Any:
    return to_class(WallarooAPITelemetryDataV1, x)
