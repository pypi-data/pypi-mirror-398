import json
import os
from typing import TYPE_CHECKING, Any, Callable, Dict, Optional, Union

from wallaroo.wallaroo_ml_ops_api_client import models

from .engine_config import (
    Acceleration,
    AccelerationWithConfig,
    Architecture,
    QaicConfig,
    QaicWithConfig,
)

if TYPE_CHECKING:
    from .model_version import ModelVersion


def _accel_to_mlops_accel(
    accel: Union[Acceleration, AccelerationWithConfig],
) -> Union[
    models.AccelerationType0,
    models.AccelerationType1,
    models.AccelerationType2,
    models.AccelerationType3,
    models.AccelerationType4,
]:
    if isinstance(accel, AccelerationWithConfig):
        val = accel._to_openapi_acceleration_with_config()
        return models.AccelerationType4.from_dict(val.to_dict())

    match accel:
        case Acceleration._None:
            return models.AccelerationType0.NONE
        case Acceleration.CUDA:
            return models.AccelerationType1.CUDA
        case Acceleration.Jetson:
            return models.AccelerationType2.JETSON
        case Acceleration.OpenVINO:
            return models.AccelerationType3.OPENVINO
        case Acceleration.QAIC:
            return _accel_to_mlops_accel(accel.default_acceleration_with_config())
        case _:
            raise ValueError(f"Unsupported acceleration type: {accel}")


class DeploymentConfig(Dict):
    def _guarantee_workspace_id(
        self, workspace_id: Optional[int]
    ) -> "DeploymentConfig":
        if workspace_id is None:
            return self
        if self.get("workspace_id", None) is None:
            self["workspace_id"] = workspace_id
        return self

    def _deploy_config_to_engine_config(self):
        from wallaroo.wallaroo_ml_ops_api_client.models import (
            EngineConfig,
            Resources,
            ResourceSpec,
            ResourcesSpec,
            SidekickConfig,
            SidekickConfigImagesType0 as Images,
        )
        from wallaroo.wallaroo_ml_ops_api_client.types import UNSET

        if self is None:
            return None

        # Engine block
        engine = self.get("engine")
        cpus = engine.get("cpu", 1.0)
        mem = engine.get("resources", {}).get("requests", {}).get("memory", "512Mi")
        arch = engine.get("arch") or str(Architecture.default())
        accel = engine.get("accel") or str(Acceleration.default())
        gpu = engine.get("gpu", 0)
        image = engine.get("image")
        resource_spec = ResourceSpec(cpus, mem)
        resources = ResourcesSpec(
            resource_spec,
            resource_spec,
            _accel_to_mlops_accel(DeploymentConfigBuilder.convert_acceleration(accel)),
            Architecture(arch),
            gpu > 0,
            image,
        )

        sidekicks = Images()
        engine_aux = self.get("engineAux")
        for name, value in engine_aux.get("images", {}).items():
            sk_requests = value.get("resources", {}).get("requests", {})
            sk_cpus = sk_requests.get("cpu", 1.0)
            sk_mem = sk_requests.get("memory", "512Mi")
            sk_arch = value.get("arch") or str(Architecture.default())
            sk_accel = value.get("accel") or str(Acceleration.default())
            sk_gpu_key = (
                "gpu.intel.com/i915" if sk_accel == "openvino" else "nvidia.com/gpu"
            )
            sk_gpu = sk_requests.get(sk_gpu_key, 0)
            sk_image = value.get("image")
            sk_resource_spec = ResourceSpec(sk_cpus, sk_mem)
            sk_resources = ResourcesSpec(
                sk_resource_spec,
                sk_resource_spec,
                _accel_to_mlops_accel(
                    DeploymentConfigBuilder.convert_acceleration(sk_accel)
                ),
                Architecture(sk_arch),
                sk_gpu > 0,
                sk_image,
            )
            sidekicks[name] = Resources(sk_resources)

        config = EngineConfig(Resources(resources), SidekickConfig(UNSET, sidekicks))

        return config


class DeploymentConfigBuilder(object):
    def __init__(self, workspace_id: Optional[int] = None) -> None:
        self._config: Dict[str, Any] = {
            "engine": {},
            "enginelb": {},
            "engineAux": {"images": {}},
            **({"workspace_id": workspace_id} if workspace_id is not None else {}),
        }

        env_config = os.environ.get("DEPLOYMENT_CONFIG", None)

        if env_config:
            conf = json.loads(env_config)
            setters: Dict[str, Callable[[Any], Any]] = {
                "image": self.image,
                "replicas": self.replica_count,
                "autoscale": self._autoscale,
                "cpus": self.cpus,
                "gpus": self.gpus,
                "node_selector": self.deployment_label,
                "memory": self.memory,
                "lb_cpus": self.lb_cpus,
                "lb_memory": self.lb_memory,
            }
            for key, set in setters.items():
                if key in conf:
                    set(conf[key])
            if "arch" in conf:
                self.arch(Architecture(conf["arch"]))
            if "accel" in conf:
                self.accel(Acceleration(conf["accel"]))

    def image(self, image: str) -> "DeploymentConfigBuilder":
        self._config["engine"]["image"] = image
        return self

    def replica_count(self, count: int) -> "DeploymentConfigBuilder":
        if (
            "autoscale" in self._config["engine"]
            and self._config["engine"]["autoscale"]["replica_max"] < count
        ):
            raise RuntimeError(
                "Replica count must be less than or equal to replica max. Use replica_autoscale_min_max to adjust this."
            )
        self._config["engine"]["replicas"] = count
        return self

    def _autoscale(self, autoscale: Dict[str, Any]):
        self._config["engine"]["autoscale"] = autoscale
        return self

    def replica_autoscale_min_max(self, maximum: int, minimum: int = 0):
        """Configures the minimum and maximum for autoscaling"""
        if minimum > maximum:
            raise RuntimeError("Minimum must be less than or equal to maximum")
        if minimum < 0:
            raise RuntimeError("Minimum must be at least 0")
        self._ensure_autoscale_config()
        if (
            "replicas" in self._config["engine"]
            and self._config["engine"]["replicas"] > maximum
        ):
            raise RuntimeError(
                "Maximum must be greater than or equal to number of replicas"
            )
        self._config["engine"]["autoscale"]["replica_min"] = minimum
        self._config["engine"]["autoscale"]["replica_max"] = maximum
        self._config["engine"]["autoscale"]["type"] = "cpu"
        return self

    def autoscale_cpu_utilization(self, cpu_utilization_percentage: int):
        """Sets the average CPU metric to scale on in a percentage"""
        if "autoscale" not in self._config["engine"]:
            print(
                "Warn: min and max not set for autoscaling. These must be set to enable autoscaling"
            )
            self._config["engine"]["autoscale"] = {}
        self._config["engine"]["autoscale"]["cpu_utilization"] = (
            cpu_utilization_percentage
        )
        return self

    def disable_autoscale(self):
        """Disables autoscaling in the deployment configuration"""
        if "autoscale" in ["engine"]:
            del self._config["engine"]["autoscale"]
        return self

    def _add_resource(
        self,
        component_stanza: Dict[str, Any],
        resource_name: str,
        value: Union[int, str],
    ) -> "DeploymentConfigBuilder":
        if "resources" not in component_stanza:
            component_stanza["resources"] = {"limits": {}, "requests": {}}
        component_stanza["resources"]["limits"][resource_name] = value
        component_stanza["resources"]["requests"][resource_name] = value
        return self

    def cpus(self, core_count: int) -> "DeploymentConfigBuilder":
        self._config["engine"]["cpu"] = core_count
        return self._add_resource(self._config["engine"], "cpu", core_count)

    def deployment_label(self, label: str) -> "DeploymentConfigBuilder":
        self._config["engine"]["node_selector"] = label
        return self

    def gpus(self, gpu_count: int) -> "DeploymentConfigBuilder":
        self._config["engine"]["gpu"] = gpu_count
        DeploymentConfigBuilder._clear_gpu_resources(self._config["engine"])
        key = (
            "gpu.intel.com/i915"
            if self._config["engine"].get("accel") == "openvino"
            else "nvidia.com/gpu"
        )
        return self._add_resource(self._config["engine"], key, gpu_count)

    def memory(self, memory_spec: str) -> "DeploymentConfigBuilder":
        return self._add_resource(self._config["engine"], "memory", memory_spec)

    def lb_cpus(self, core_count: int) -> "DeploymentConfigBuilder":
        return self._add_resource(self._config["enginelb"], "cpu", core_count)

    def lb_memory(self, memory_spec: int) -> "DeploymentConfigBuilder":
        return self._add_resource(self._config["enginelb"], "memory", memory_spec)

    def arch(self, arch: Optional[Architecture] = None) -> "DeploymentConfigBuilder":
        if arch is None:
            self._config["engine"].pop("arch", None)
        else:
            self._config["engine"]["arch"] = str(arch)
        return self

    def accel(self, accel: Optional[Acceleration] = None) -> "DeploymentConfigBuilder":
        old_accel = Acceleration(
            self._config["engine"].get("accel", Acceleration.default())
        )
        if accel is None:
            self._config["engine"].pop("accel", None)
        else:
            self._config["engine"]["accel"] = str(accel)
        DeploymentConfigBuilder._adjust_gpu_resources(
            self._config["engine"], accel or Acceleration.default(), old_accel
        )
        return self

    def python_load_timeout_secs(self, timeout_secs: int) -> "DeploymentConfigBuilder":
        if "python" not in self._config["engine"]:
            self._config["engine"]["python"] = {}
        self._config["engine"]["python"]["load_timeout_millis"] = timeout_secs * 1000
        return self

    def _guarantee_sidekick_stanza(
        self, model_version: "ModelVersion"
    ) -> Dict[str, Any]:
        model_uid = model_version.uid()
        if model_uid not in self._config["engineAux"]["images"]:
            self._config["engineAux"]["images"][model_uid] = {}
        return self._config["engineAux"]["images"][model_uid]

    def sidekick_gpus(
        self, model_version: "ModelVersion", gpu_count: int
    ) -> "DeploymentConfigBuilder":
        """Sets the number of GPUs to be used for the model's sidekick container. Only affects
        image-based models (e.g. MLFlow models) in a deployment.

        :param ModelVersion model_version: The sidekick model to configure.
        :param int core_count: Number of GPUs to use in this sidekick.
        :return: This DeploymentConfigBuilder instance for chaining."""

        accel = model_version.accel()
        sidekick = self._guarantee_sidekick_stanza(model_version)
        DeploymentConfigBuilder._clear_gpu_resources(sidekick)
        if isinstance(accel, dict):
            accel = DeploymentConfigBuilder.convert_acceleration_dict_to_qaic(accel)
        key = DeploymentConfigBuilder._get_gpu_resource(accel)
        return self._add_resource(sidekick, key, gpu_count)

    def sidekick_cpus(
        self, model_version: "ModelVersion", core_count: int
    ) -> "DeploymentConfigBuilder":
        """Sets the number of CPUs to be used for the model's sidekick container. Only affects
        image-based models (e.g. MLFlow models) in a deployment.

        :param ModelVersion model_version: The sidekick model to configure.
        :param int core_count: Number of CPU cores to use in this sidekick.
        :return: This DeploymentConfigBuilder instance for chaining."""

        return self._add_resource(
            self._guarantee_sidekick_stanza(model_version), "cpu", core_count
        )

    def sidekick_memory(
        self, model_version: "ModelVersion", memory_spec: str
    ) -> "DeploymentConfigBuilder":
        """Sets the memory to be used for the model's sidekick container. Only affects
        image-based models (e.g. MLFlow models) in a deployment.

        :param ModelVersion model_version: The sidekick model to configure.
        :param str memory_spec: Specification of amount of memory (e.g., "2Gi", "500Mi") to use in
        this sidekick.
        :return: This DeploymentConfigBuilder instance for chaining."""

        return self._add_resource(
            self._guarantee_sidekick_stanza(model_version), "memory", memory_spec
        )

    def sidekick_env(
        self, model_version: "ModelVersion", environment: Dict[str, str]
    ) -> "DeploymentConfigBuilder":
        """Sets the environment variables to be set for the model's sidekick container. Only affects
        image-based models (e.g. MLFlow models) in a deployment.

        :param ModelVersion model_version: The sidekick model to configure.
        :param Dict[str, str] environment: Dictionary of environment variables names and their
        corresponding values to be set in the sidekick container.
        :return: This DeploymentConfigBuilder instance for chaining."""

        stanza = self._guarantee_sidekick_stanza(model_version)
        stanza["env"] = []
        for name, value in environment.items():
            stanza["env"].append({"name": name, "value": value})

        return self

    def sidekick_arch(
        self, model_version: "ModelVersion", arch: Optional[Architecture] = None
    ) -> "DeploymentConfigBuilder":
        """Sets the machine architecture for the model's sidekick container. Only affects
        image-based models (e.g. MLFlow models) in a deployment.

        :param model_version: ModelVersion: The sidekick model to configure.
        :param arch: Optional[Architecture]: Machine architecture for this sidekick.
        :return: This DeploymentConfigBuilder instance for chaining."""

        config = self._guarantee_sidekick_stanza(model_version)
        if arch is None:
            config.pop("arch", None)
        else:
            config["arch"] = str(arch)
        return self

    def sidekick_accel(
        self,
        model_version: "ModelVersion",
        accel: Optional[Union[Acceleration, AccelerationWithConfig]] = None,
    ) -> "DeploymentConfigBuilder":
        """Sets the acceleration option for the model's sidekick container. Only affects
        image-based models (e.g. MLFlow models) in a deployment.

        :param model_version: ModelVersion: The sidekick model to configure.
        :param accel: Optional[Union[Acceleration, AccelerationWithConfig]]: Acceleration option for this sidekick.
        :return: This DeploymentConfigBuilder instance for chaining."""

        config = self._guarantee_sidekick_stanza(model_version)

        old_accel = config.get("accel", Acceleration.default())

        if isinstance(old_accel, dict):
            old_accel = DeploymentConfigBuilder.convert_acceleration_dict_to_qaic(
                old_accel
            )
        else:
            old_accel = Acceleration(old_accel)

        if accel is None:
            config.pop("accel", None)
        else:
            config["accel"] = str(accel)

        DeploymentConfigBuilder._adjust_gpu_resources(
            config, accel or Acceleration.default(), old_accel
        )

        return self

    def scale_up_queue_depth(self, queue_depth: int) -> "DeploymentConfigBuilder":
        """
        Configure the scale_up_queue_depth threshold as an autoscaling trigger.

        This method sets a queue depth threshold above which all pipeline components
        (including the engine and LLM sidekicks) will incrementally scale up.

        The scale_up_queue_depth is calculated as:
        (number of requests in queue + requests being processed) / number of available replicas
        over a scaling window.

        Notes:
            - This parameter must be configured to activate queue-based autoscaling.
            - No default value is provided.
            - When configured, scale_up_queue_depth overrides the default autoscaling
              trigger (cpu_utilization).
            - The setting applies to all components of the pipeline.
            - When set, scale_down_queue_depth is automatically set to 1 if not already configured.

        :param queue_depth (int): The threshold value for queue-based autoscaling.
        :return: DeploymentConfigBuilder: The current instance for method chaining.
        """
        self._ensure_autoscale_config()
        self._config["engine"]["autoscale"]["scale_up_queue_depth"] = queue_depth
        self._config["engine"]["autoscale"]["type"] = "queue"

        # Ensure scale_down_queue_depth is set to 1 if not already configured
        if "scale_down_queue_depth" not in self._config["engine"]["autoscale"]:
            self._config["engine"]["autoscale"]["scale_down_queue_depth"] = 1

        return self

    def scale_down_queue_depth(
        self, queue_depth: Optional[int] = None
    ) -> "DeploymentConfigBuilder":
        """
        Configure the scale_down_queue_depth threshold as an autoscaling trigger.

        This method sets a queue depth threshold below which all pipeline components
        (including the engine and LLM sidekicks) will incrementally scale down.

        The scale_down_queue_depth is calculated as:
        (number of requests in queue + requests being processed) / number of available replicas
        over a scaling window.

        Notes:
            - This parameter is optional and defaults to 1 if not set.
            - scale_down_queue_depth is only applicable when scale_up_queue_depth is configured.
            - The setting applies to all components of the pipeline.
            - This threshold helps prevent unnecessary scaling down when the workload is still
              significant but below the scale-up threshold.

        :param queue_depth (int): The threshold value for queue-based downscaling.
        :return: DeploymentConfigBuilder: The current instance for method chaining.

        :raises ValueError: If scale_up_queue_depth is not configured.
        """
        self._ensure_autoscale_config()
        self._ensure_scale_up_queue_depth_is_configured("scale_down_queue_depth")
        self._config["engine"]["autoscale"]["scale_down_queue_depth"] = (
            queue_depth if queue_depth is not None else 1
        )

        return self

    def autoscaling_window(
        self, window_seconds: Optional[int] = None
    ) -> "DeploymentConfigBuilder":
        """
        Configure the autoscaling window for incrementally scaling up/down pipeline components.

        This method sets the time window over which the autoscaling metrics are evaluated
        for making scaling decisions. It applies to all components of the pipeline,
        including the engine and LLM sidekicks.

        Notes:
            - The default value is 300 seconds if not specified.
            - This setting is only applicable when scale_up_queue_depth is configured.
            - The autoscaling window helps smooth out short-term fluctuations in workload
              and prevents rapid scaling events.

        :param window_seconds: Optional[int], the duration of the autoscaling window in seconds.
                               If None, the default value of 300 seconds is used.
        :return: DeploymentConfigBuilder: The current instance for method chaining.

        :raises ValueError: If scale_up_queue_depth is not configured.
        """
        self._ensure_autoscale_config()
        self._ensure_scale_up_queue_depth_is_configured("autoscaling_window")

        # Use the default value of 300 seconds if window_seconds is None
        self._config["engine"]["autoscale"]["autoscaling_window"] = (
            window_seconds if window_seconds is not None else 300
        )

        return self

    @staticmethod
    def _adjust_gpu_resources(
        component: Dict[str, Any],
        new_accel: Union[Acceleration, AccelerationWithConfig],
        old_accel: Union[Acceleration, AccelerationWithConfig],
    ) -> None:
        resources = component.get("resources", {"limits": {}, "requests": {}})
        if (
            new_accel
            not in (Acceleration.OpenVINO, Acceleration.QAIC, Acceleration.CUDA)
            or new_accel == old_accel
        ):
            return

        new_key = DeploymentConfigBuilder._get_gpu_resource(new_accel)
        old_key = DeploymentConfigBuilder._get_gpu_resource(old_accel)

        limit = resources["limits"].pop(old_key, None)
        request = resources["requests"].pop(old_key, None)
        if limit is not None:
            resources["limits"][new_key] = limit
        if request is not None:
            resources["requests"][new_key] = request

    @staticmethod
    def _get_gpu_resource(accel: Union[Acceleration, AccelerationWithConfig]) -> str:
        if isinstance(accel, AccelerationWithConfig):
            match accel.accel:
                case Acceleration.QAIC:
                    return "qualcomm.com/qaic"
                case _:
                    return "nvidia.com/gpu"
        match accel:
            case Acceleration.OpenVINO:
                return "gpu.intel.com/i915"
            case Acceleration.QAIC:
                return "qualcomm.com/qaic"
            case _:
                return "nvidia.com/gpu"

    @staticmethod
    def _clear_gpu_resources(component: Dict[str, Any]):
        resources = component.get("resources", {"limits": {}, "requests": {}})
        resources["limits"].pop("gpu.intel.com/i915", None)
        resources["limits"].pop("nvidia.com/gpu", None)
        resources["limits"].pop("qualcomm.com/qaic", None)
        resources["requests"].pop("gpu.intel.com/i915", None)
        resources["requests"].pop("nvidia.com/gpu", None)
        resources["requests"].pop("qualcomm.com/qaic", None)

    def _ensure_autoscale_config(self):
        """Ensure that the 'autoscale' key exists in the engine configuration."""
        if "autoscale" not in self._config["engine"]:
            self._config["engine"]["autoscale"] = {}

    def _ensure_scale_up_queue_depth_is_configured(self, feature_name: str):
        """
        Check if scale_up_queue_depth is configured in the autoscale settings.

        :param feature_name: str, the name of the feature being configured
        :raises ValueError: If scale_up_queue_depth is not configured
        """
        if "scale_up_queue_depth" not in self._config["engine"].get("autoscale", {}):
            raise ValueError(
                f"{feature_name} is only applicable when scale_up_queue_depth is configured."
            )

    @staticmethod
    def convert_acceleration(
        accel_obj: Union[str, dict],
    ) -> Union[Acceleration, AccelerationWithConfig]:
        """
        Convert the acceleration string to an Acceleration or AccelerationWithConfig object.

        :param accel_str: str, the acceleration string to check
        :return: Union[Acceleration, AccelerationWithConfig], the acceleration type
        """
        if isinstance(accel_obj, dict):
            if Acceleration.QAIC in accel_obj:
                return QaicWithConfig(
                    config=QaicConfig(**accel_obj.get(Acceleration.QAIC, {}))
                )
        try:
            if isinstance(accel_obj, str):
                accel_obj = json.loads(accel_obj)
            if isinstance(accel_obj, dict) and Acceleration.QAIC in accel_obj:
                return QaicWithConfig(
                    config=QaicConfig(**accel_obj.get(Acceleration.QAIC, {}))
                )
        except json.JSONDecodeError:
            pass

        return Acceleration(accel_obj)

    @staticmethod
    def convert_acceleration_to_string(accel_obj: Union[str, dict]) -> str:
        """
        Convert an Acceleration object to a valid string for deployment.

        :param accel_obj: Union[str, dict], the acceleration to be converted
        return: str, the stringified acceleration
        """
        if isinstance(accel_obj, dict):
            return json.dumps(accel_obj).replace("'", '"')
        return accel_obj

    @staticmethod
    def convert_acceleration_dict_to_qaic(accel_obj: dict) -> QaicWithConfig:
        """
        Convert an acceleration dict to a QaicWithConfig object.
        """
        qaic_config = accel_obj.get(Acceleration.QAIC, {})
        return QaicWithConfig(config=QaicConfig(**qaic_config))

    def build(self) -> DeploymentConfig:
        engine_node_selector = self._config["engine"].get("node_selector", None)
        if engine_node_selector:
            for model in self._config["engineAux"]["images"].values():
                model.setdefault("node_selector", engine_node_selector)
        return DeploymentConfig(self._config)
