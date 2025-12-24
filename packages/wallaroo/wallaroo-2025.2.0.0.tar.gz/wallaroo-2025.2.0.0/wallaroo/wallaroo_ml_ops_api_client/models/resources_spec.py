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
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.acceleration_type_4 import AccelerationType4
    from ..models.resource_spec import ResourceSpec


T = TypeVar("T", bound="ResourcesSpec")


@_attrs_define
class ResourcesSpec:
    """
    Attributes:
        limits (ResourceSpec):
        requests (ResourceSpec):
        accel (Union['AccelerationType4', AccelerationType0, AccelerationType1, AccelerationType2, AccelerationType3,
            Unset]): Acceleration options
        arch (Union[Unset, Architecture]): Processor architecture to execute on
        gpu (Union[Unset, bool]):
        image (Union[None, Unset, str]):
    """

    limits: "ResourceSpec"
    requests: "ResourceSpec"
    accel: Union[
        "AccelerationType4",
        AccelerationType0,
        AccelerationType1,
        AccelerationType2,
        AccelerationType3,
        Unset,
    ] = UNSET
    arch: Union[Unset, Architecture] = UNSET
    gpu: Union[Unset, bool] = UNSET
    image: Union[None, Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        limits = self.limits.to_dict()

        requests = self.requests.to_dict()

        accel: Union[Unset, dict[str, Any], str]
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
        else:
            accel = self.accel.to_dict()

        arch: Union[Unset, str] = UNSET
        if not isinstance(self.arch, Unset):
            arch = self.arch.value

        gpu = self.gpu

        image: Union[None, Unset, str]
        if isinstance(self.image, Unset):
            image = UNSET
        else:
            image = self.image

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "limits": limits,
                "requests": requests,
            }
        )
        if accel is not UNSET:
            field_dict["accel"] = accel
        if arch is not UNSET:
            field_dict["arch"] = arch
        if gpu is not UNSET:
            field_dict["gpu"] = gpu
        if image is not UNSET:
            field_dict["image"] = image

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.acceleration_type_4 import AccelerationType4
        from ..models.resource_spec import ResourceSpec

        d = dict(src_dict)
        limits = ResourceSpec.from_dict(d.pop("limits"))

        requests = ResourceSpec.from_dict(d.pop("requests"))

        def _parse_accel(
            data: object,
        ) -> Union[
            "AccelerationType4",
            AccelerationType0,
            AccelerationType1,
            AccelerationType2,
            AccelerationType3,
            Unset,
        ]:
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
            if not isinstance(data, dict):
                raise TypeError()
            componentsschemas_acceleration_type_4 = AccelerationType4.from_dict(data)

            return componentsschemas_acceleration_type_4

        accel = _parse_accel(d.pop("accel", UNSET))

        _arch = d.pop("arch", UNSET)
        arch: Union[Unset, Architecture]
        if isinstance(_arch, Unset):
            arch = UNSET
        else:
            arch = Architecture(_arch)

        gpu = d.pop("gpu", UNSET)

        def _parse_image(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        image = _parse_image(d.pop("image", UNSET))

        resources_spec = cls(
            limits=limits,
            requests=requests,
            accel=accel,
            arch=arch,
            gpu=gpu,
            image=image,
        )

        resources_spec.additional_properties = d
        return resources_spec

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
