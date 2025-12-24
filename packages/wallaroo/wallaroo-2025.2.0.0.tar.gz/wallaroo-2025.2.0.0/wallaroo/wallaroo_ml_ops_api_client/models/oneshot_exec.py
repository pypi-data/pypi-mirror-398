from collections.abc import Mapping
from typing import (
    TYPE_CHECKING,
    Any,
    TypeVar,
    Union,
    cast,
)
from uuid import UUID

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..models.architecture import Architecture
from ..models.restart_policy import RestartPolicy
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.event_base_extra_env_vars import EventBaseExtraEnvVars
    from ..models.oneshot_exec_exec_type import OneshotExecExecType


T = TypeVar("T", bound="OneshotExec")


@_attrs_define
class OneshotExec:
    """
    Attributes:
        auth_init (bool):
        id (Union[UUID, int]):
        image (str):
        image_tag (str):
        workspace_id (int):
        flavor (str):
        reap_threshold_secs (int):
        arch (Union[Architecture, None, Unset]):
        bind_secrets (Union[Unset, list[str]]):
        extra_env_vars (Union[Unset, EventBaseExtraEnvVars]):
        completions (Union[None, Unset, int]):
        exec_type (Union[Unset, OneshotExecExecType]):
        indexed_job (Union[None, Unset, bool]):
        ns_prefix (Union[None, Unset, str]):
        parallelism (Union[None, Unset, int]):
        restart_policy (Union[None, RestartPolicy, Unset]):
    """

    auth_init: bool
    id: Union[UUID, int]
    image: str
    image_tag: str
    workspace_id: int
    flavor: str
    reap_threshold_secs: int
    arch: Union[Architecture, None, Unset] = UNSET
    bind_secrets: Union[Unset, list[str]] = UNSET
    extra_env_vars: Union[Unset, "EventBaseExtraEnvVars"] = UNSET
    completions: Union[None, Unset, int] = UNSET
    exec_type: Union[Unset, "OneshotExecExecType"] = UNSET
    indexed_job: Union[None, Unset, bool] = UNSET
    ns_prefix: Union[None, Unset, str] = UNSET
    parallelism: Union[None, Unset, int] = UNSET
    restart_policy: Union[None, RestartPolicy, Unset] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        auth_init = self.auth_init

        id: Union[int, str]
        if isinstance(self.id, UUID):
            id = str(self.id)
        else:
            id = self.id

        image = self.image

        image_tag = self.image_tag

        workspace_id = self.workspace_id

        flavor = self.flavor

        reap_threshold_secs = self.reap_threshold_secs

        arch: Union[None, Unset, str]
        if isinstance(self.arch, Unset):
            arch = UNSET
        elif isinstance(self.arch, Architecture):
            arch = self.arch.value
        else:
            arch = self.arch

        bind_secrets: Union[Unset, list[str]] = UNSET
        if not isinstance(self.bind_secrets, Unset):
            bind_secrets = self.bind_secrets

        extra_env_vars: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.extra_env_vars, Unset):
            extra_env_vars = self.extra_env_vars.to_dict()

        completions: Union[None, Unset, int]
        if isinstance(self.completions, Unset):
            completions = UNSET
        else:
            completions = self.completions

        exec_type: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.exec_type, Unset):
            exec_type = self.exec_type.to_dict()

        indexed_job: Union[None, Unset, bool]
        if isinstance(self.indexed_job, Unset):
            indexed_job = UNSET
        else:
            indexed_job = self.indexed_job

        ns_prefix: Union[None, Unset, str]
        if isinstance(self.ns_prefix, Unset):
            ns_prefix = UNSET
        else:
            ns_prefix = self.ns_prefix

        parallelism: Union[None, Unset, int]
        if isinstance(self.parallelism, Unset):
            parallelism = UNSET
        else:
            parallelism = self.parallelism

        restart_policy: Union[None, Unset, str]
        if isinstance(self.restart_policy, Unset):
            restart_policy = UNSET
        elif isinstance(self.restart_policy, RestartPolicy):
            restart_policy = self.restart_policy.value
        else:
            restart_policy = self.restart_policy

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "auth_init": auth_init,
                "id": id,
                "image": image,
                "image_tag": image_tag,
                "workspace_id": workspace_id,
                "flavor": flavor,
                "reap_threshold_secs": reap_threshold_secs,
            }
        )
        if arch is not UNSET:
            field_dict["arch"] = arch
        if bind_secrets is not UNSET:
            field_dict["bind_secrets"] = bind_secrets
        if extra_env_vars is not UNSET:
            field_dict["extra_env_vars"] = extra_env_vars
        if completions is not UNSET:
            field_dict["completions"] = completions
        if exec_type is not UNSET:
            field_dict["exec_type"] = exec_type
        if indexed_job is not UNSET:
            field_dict["indexed_job"] = indexed_job
        if ns_prefix is not UNSET:
            field_dict["ns_prefix"] = ns_prefix
        if parallelism is not UNSET:
            field_dict["parallelism"] = parallelism
        if restart_policy is not UNSET:
            field_dict["restart_policy"] = restart_policy

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.event_base_extra_env_vars import EventBaseExtraEnvVars
        from ..models.oneshot_exec_exec_type import OneshotExecExecType

        d = dict(src_dict)
        auth_init = d.pop("auth_init")

        def _parse_id(data: object) -> Union[UUID, int]:
            try:
                if not isinstance(data, str):
                    raise TypeError()
                componentsschemas_event_id_type_1 = UUID(data)

                return componentsschemas_event_id_type_1
            except:  # noqa: E722
                pass
            return cast(Union[UUID, int], data)

        id = _parse_id(d.pop("id"))

        image = d.pop("image")

        image_tag = d.pop("image_tag")

        workspace_id = d.pop("workspace_id")

        flavor = d.pop("flavor")

        reap_threshold_secs = d.pop("reap_threshold_secs")

        def _parse_arch(data: object) -> Union[Architecture, None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                arch_type_1 = Architecture(data)

                return arch_type_1
            except:  # noqa: E722
                pass
            return cast(Union[Architecture, None, Unset], data)

        arch = _parse_arch(d.pop("arch", UNSET))

        bind_secrets = cast(list[str], d.pop("bind_secrets", UNSET))

        _extra_env_vars = d.pop("extra_env_vars", UNSET)
        extra_env_vars: Union[Unset, EventBaseExtraEnvVars]
        if isinstance(_extra_env_vars, Unset):
            extra_env_vars = UNSET
        else:
            extra_env_vars = EventBaseExtraEnvVars.from_dict(_extra_env_vars)

        def _parse_completions(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        completions = _parse_completions(d.pop("completions", UNSET))

        _exec_type = d.pop("exec_type", UNSET)
        exec_type: Union[Unset, OneshotExecExecType]
        if isinstance(_exec_type, Unset):
            exec_type = UNSET
        else:
            exec_type = OneshotExecExecType.from_dict(_exec_type)

        def _parse_indexed_job(data: object) -> Union[None, Unset, bool]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, bool], data)

        indexed_job = _parse_indexed_job(d.pop("indexed_job", UNSET))

        def _parse_ns_prefix(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        ns_prefix = _parse_ns_prefix(d.pop("ns_prefix", UNSET))

        def _parse_parallelism(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        parallelism = _parse_parallelism(d.pop("parallelism", UNSET))

        def _parse_restart_policy(data: object) -> Union[None, RestartPolicy, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                restart_policy_type_1 = RestartPolicy(data)

                return restart_policy_type_1
            except:  # noqa: E722
                pass
            return cast(Union[None, RestartPolicy, Unset], data)

        restart_policy = _parse_restart_policy(d.pop("restart_policy", UNSET))

        oneshot_exec = cls(
            auth_init=auth_init,
            id=id,
            image=image,
            image_tag=image_tag,
            workspace_id=workspace_id,
            flavor=flavor,
            reap_threshold_secs=reap_threshold_secs,
            arch=arch,
            bind_secrets=bind_secrets,
            extra_env_vars=extra_env_vars,
            completions=completions,
            exec_type=exec_type,
            indexed_job=indexed_job,
            ns_prefix=ns_prefix,
            parallelism=parallelism,
            restart_policy=restart_policy,
        )

        oneshot_exec.additional_properties = d
        return oneshot_exec

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
