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
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.event_base_extra_env_vars import EventBaseExtraEnvVars


T = TypeVar("T", bound="NetworkServiceExec")


@_attrs_define
class NetworkServiceExec:
    """
    Attributes:
        auth_init (bool):
        id (Union[UUID, int]):
        image (str):
        image_tag (str):
        workspace_id (int):
        flavor (str):
        arch (Union[Architecture, None, Unset]):
        bind_secrets (Union[Unset, list[str]]):
        extra_env_vars (Union[Unset, EventBaseExtraEnvVars]):
    """

    auth_init: bool
    id: Union[UUID, int]
    image: str
    image_tag: str
    workspace_id: int
    flavor: str
    arch: Union[Architecture, None, Unset] = UNSET
    bind_secrets: Union[Unset, list[str]] = UNSET
    extra_env_vars: Union[Unset, "EventBaseExtraEnvVars"] = UNSET
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
            }
        )
        if arch is not UNSET:
            field_dict["arch"] = arch
        if bind_secrets is not UNSET:
            field_dict["bind_secrets"] = bind_secrets
        if extra_env_vars is not UNSET:
            field_dict["extra_env_vars"] = extra_env_vars

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.event_base_extra_env_vars import EventBaseExtraEnvVars

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

        network_service_exec = cls(
            auth_init=auth_init,
            id=id,
            image=image,
            image_tag=image_tag,
            workspace_id=workspace_id,
            flavor=flavor,
            arch=arch,
            bind_secrets=bind_secrets,
            extra_env_vars=extra_env_vars,
        )

        network_service_exec.additional_properties = d
        return network_service_exec

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
