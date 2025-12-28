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

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.auto_scale_config_type_0 import AutoScaleConfigType0
    from ..models.auto_scale_config_type_1 import AutoScaleConfigType1
    from ..models.auto_scale_config_type_2 import AutoScaleConfigType2
    from ..models.auto_scale_config_type_3 import AutoScaleConfigType3
    from ..models.sidekick_config_images_type_0 import SidekickConfigImagesType0


T = TypeVar("T", bound="SidekickConfig")


@_attrs_define
class SidekickConfig:
    """
    Attributes:
        autoscale (Union['AutoScaleConfigType0', 'AutoScaleConfigType1', 'AutoScaleConfigType2', 'AutoScaleConfigType3',
            Unset]):
        images (Union['SidekickConfigImagesType0', None, Unset]):
    """

    autoscale: Union[
        "AutoScaleConfigType0",
        "AutoScaleConfigType1",
        "AutoScaleConfigType2",
        "AutoScaleConfigType3",
        Unset,
    ] = UNSET
    images: Union["SidekickConfigImagesType0", None, Unset] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.auto_scale_config_type_0 import AutoScaleConfigType0
        from ..models.auto_scale_config_type_1 import AutoScaleConfigType1
        from ..models.auto_scale_config_type_2 import AutoScaleConfigType2
        from ..models.sidekick_config_images_type_0 import SidekickConfigImagesType0

        autoscale: Union[Unset, dict[str, Any]]
        if isinstance(self.autoscale, Unset):
            autoscale = UNSET
        elif isinstance(self.autoscale, AutoScaleConfigType0):
            autoscale = self.autoscale.to_dict()
        elif isinstance(self.autoscale, AutoScaleConfigType1):
            autoscale = self.autoscale.to_dict()
        elif isinstance(self.autoscale, AutoScaleConfigType2):
            autoscale = self.autoscale.to_dict()
        else:
            autoscale = self.autoscale.to_dict()

        images: Union[None, Unset, dict[str, Any]]
        if isinstance(self.images, Unset):
            images = UNSET
        elif isinstance(self.images, SidekickConfigImagesType0):
            images = self.images.to_dict()
        else:
            images = self.images

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if autoscale is not UNSET:
            field_dict["autoscale"] = autoscale
        if images is not UNSET:
            field_dict["images"] = images

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.auto_scale_config_type_0 import AutoScaleConfigType0
        from ..models.auto_scale_config_type_1 import AutoScaleConfigType1
        from ..models.auto_scale_config_type_2 import AutoScaleConfigType2
        from ..models.auto_scale_config_type_3 import AutoScaleConfigType3
        from ..models.sidekick_config_images_type_0 import SidekickConfigImagesType0

        d = dict(src_dict)

        def _parse_autoscale(
            data: object,
        ) -> Union[
            "AutoScaleConfigType0",
            "AutoScaleConfigType1",
            "AutoScaleConfigType2",
            "AutoScaleConfigType3",
            Unset,
        ]:
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_auto_scale_config_type_0 = (
                    AutoScaleConfigType0.from_dict(data)
                )

                return componentsschemas_auto_scale_config_type_0
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_auto_scale_config_type_1 = (
                    AutoScaleConfigType1.from_dict(data)
                )

                return componentsschemas_auto_scale_config_type_1
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_auto_scale_config_type_2 = (
                    AutoScaleConfigType2.from_dict(data)
                )

                return componentsschemas_auto_scale_config_type_2
            except:  # noqa: E722
                pass
            if not isinstance(data, dict):
                raise TypeError()
            componentsschemas_auto_scale_config_type_3 = AutoScaleConfigType3.from_dict(
                data
            )

            return componentsschemas_auto_scale_config_type_3

        autoscale = _parse_autoscale(d.pop("autoscale", UNSET))

        def _parse_images(
            data: object,
        ) -> Union["SidekickConfigImagesType0", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                images_type_0 = SidekickConfigImagesType0.from_dict(data)

                return images_type_0
            except:  # noqa: E722
                pass
            return cast(Union["SidekickConfigImagesType0", None, Unset], data)

        images = _parse_images(d.pop("images", UNSET))

        sidekick_config = cls(
            autoscale=autoscale,
            images=images,
        )

        sidekick_config.additional_properties = d
        return sidekick_config

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
