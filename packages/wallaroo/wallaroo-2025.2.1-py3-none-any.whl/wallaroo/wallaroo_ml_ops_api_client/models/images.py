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
    from ..models.images_images_type_0 import ImagesImagesType0


T = TypeVar("T", bound="Images")


@_attrs_define
class Images:
    """
    Attributes:
        images (Union['ImagesImagesType0', None, Unset]):
    """

    images: Union["ImagesImagesType0", None, Unset] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.images_images_type_0 import ImagesImagesType0

        images: Union[None, Unset, dict[str, Any]]
        if isinstance(self.images, Unset):
            images = UNSET
        elif isinstance(self.images, ImagesImagesType0):
            images = self.images.to_dict()
        else:
            images = self.images

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if images is not UNSET:
            field_dict["images"] = images

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.images_images_type_0 import ImagesImagesType0

        d = dict(src_dict)

        def _parse_images(data: object) -> Union["ImagesImagesType0", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                images_type_0 = ImagesImagesType0.from_dict(data)

                return images_type_0
            except:  # noqa: E722
                pass
            return cast(Union["ImagesImagesType0", None, Unset], data)

        images = _parse_images(d.pop("images", UNSET))

        images = cls(
            images=images,
        )

        images.additional_properties = d
        return images

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
