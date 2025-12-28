from collections.abc import Mapping
from typing import (
    TYPE_CHECKING,
    Any,
    TypeVar,
    Union,
    cast,
)

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..models.acceleration_type_0 import AccelerationType0
from ..models.acceleration_type_1 import AccelerationType1
from ..models.acceleration_type_2 import AccelerationType2
from ..models.acceleration_type_3 import AccelerationType3
from ..models.architecture import Architecture
from ..models.framework import Framework
from ..models.python_version import PythonVersion
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.acceleration_type_4 import AccelerationType4
    from ..models.framework_config_type_0 import FrameworkConfigType0
    from ..models.framework_config_type_1 import FrameworkConfigType1


T = TypeVar("T", bound="Conversion")


@_attrs_define
class Conversion:
    """
    Attributes:
        framework (Framework):
        requirements (list[str]):
        accel (Union['AccelerationType4', AccelerationType0, AccelerationType1, AccelerationType2, AccelerationType3,
            None, Unset]):
        arch (Union[Architecture, None, Unset]):
        framework_config (Union['FrameworkConfigType0', 'FrameworkConfigType1', None, Unset]):
        python_version (Union[Unset, PythonVersion]):
    """

    framework: Framework
    requirements: list[str]
    accel: Union[
        "AccelerationType4",
        AccelerationType0,
        AccelerationType1,
        AccelerationType2,
        AccelerationType3,
        None,
        Unset,
    ] = UNSET
    arch: Union[Architecture, None, Unset] = UNSET
    framework_config: Union[
        "FrameworkConfigType0", "FrameworkConfigType1", None, Unset
    ] = UNSET
    python_version: Union[Unset, PythonVersion] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.acceleration_type_4 import AccelerationType4
        from ..models.framework_config_type_0 import FrameworkConfigType0
        from ..models.framework_config_type_1 import FrameworkConfigType1

        framework = self.framework.value

        requirements = self.requirements

        accel: Union[None, Unset, dict[str, Any], str]
        if isinstance(self.accel, Unset):
            accel = UNSET
        elif isinstance(self.accel, AccelerationType0):
            accel = self.accel.value
        elif isinstance(self.accel, AccelerationType1):
            accel = self.accel.value
        elif isinstance(self.accel, AccelerationType2):
            accel = self.accel.value
        elif isinstance(self.accel, AccelerationType3):
            accel = self.accel.value
        elif isinstance(self.accel, AccelerationType4):
            accel = self.accel.to_dict()
        else:
            accel = self.accel

        arch: Union[None, Unset, str]
        if isinstance(self.arch, Unset):
            arch = UNSET
        elif isinstance(self.arch, Architecture):
            arch = self.arch.value
        else:
            arch = self.arch

        framework_config: Union[None, Unset, dict[str, Any]]
        if isinstance(self.framework_config, Unset):
            framework_config = UNSET
        elif isinstance(self.framework_config, FrameworkConfigType0):
            framework_config = self.framework_config.to_dict()
        elif isinstance(self.framework_config, FrameworkConfigType1):
            framework_config = self.framework_config.to_dict()
        else:
            framework_config = self.framework_config

        python_version: Union[Unset, str] = UNSET
        if not isinstance(self.python_version, Unset):
            python_version = self.python_version.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "framework": framework,
                "requirements": requirements,
            }
        )
        if accel is not UNSET:
            field_dict["accel"] = accel
        if arch is not UNSET:
            field_dict["arch"] = arch
        if framework_config is not UNSET:
            field_dict["framework_config"] = framework_config
        if python_version is not UNSET:
            field_dict["python_version"] = python_version

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.acceleration_type_4 import AccelerationType4
        from ..models.framework_config_type_0 import FrameworkConfigType0
        from ..models.framework_config_type_1 import FrameworkConfigType1

        d = dict(src_dict)
        framework = Framework(d.pop("framework"))

        requirements = cast(list[str], d.pop("requirements"))

        def _parse_accel(
            data: object,
        ) -> Union[
            "AccelerationType4",
            AccelerationType0,
            AccelerationType1,
            AccelerationType2,
            AccelerationType3,
            None,
            Unset,
        ]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                componentsschemas_acceleration_type_0 = AccelerationType0(data)

                return componentsschemas_acceleration_type_0
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, str):
                    raise TypeError()
                componentsschemas_acceleration_type_1 = AccelerationType1(data)

                return componentsschemas_acceleration_type_1
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, str):
                    raise TypeError()
                componentsschemas_acceleration_type_2 = AccelerationType2(data)

                return componentsschemas_acceleration_type_2
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, str):
                    raise TypeError()
                componentsschemas_acceleration_type_3 = AccelerationType3(data)

                return componentsschemas_acceleration_type_3
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_acceleration_type_4 = AccelerationType4.from_dict(
                    data
                )

                return componentsschemas_acceleration_type_4
            except:  # noqa: E722
                pass
            return cast(
                Union[
                    "AccelerationType4",
                    AccelerationType0,
                    AccelerationType1,
                    AccelerationType2,
                    AccelerationType3,
                    None,
                    Unset,
                ],
                data,
            )

        accel = _parse_accel(d.pop("accel", UNSET))

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

        def _parse_framework_config(
            data: object,
        ) -> Union["FrameworkConfigType0", "FrameworkConfigType1", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_framework_config_type_0 = (
                    FrameworkConfigType0.from_dict(data)
                )

                return componentsschemas_framework_config_type_0
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_framework_config_type_1 = (
                    FrameworkConfigType1.from_dict(data)
                )

                return componentsschemas_framework_config_type_1
            except:  # noqa: E722
                pass
            return cast(
                Union["FrameworkConfigType0", "FrameworkConfigType1", None, Unset], data
            )

        framework_config = _parse_framework_config(d.pop("framework_config", UNSET))

        _python_version = d.pop("python_version", UNSET)
        python_version: Union[Unset, PythonVersion]
        if isinstance(_python_version, Unset):
            python_version = UNSET
        else:
            python_version = PythonVersion(_python_version)

        conversion = cls(
            framework=framework,
            requirements=requirements,
            accel=accel,
            arch=arch,
            framework_config=framework_config,
            python_version=python_version,
        )

        conversion.additional_properties = d
        return conversion

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
