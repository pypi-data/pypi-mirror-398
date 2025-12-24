from collections.abc import Mapping
from typing import (
    TYPE_CHECKING,
    Any,
    TypeVar,
)

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

if TYPE_CHECKING:
    from ..models.data_origin import DataOrigin
    from ..models.data_path import DataPath


T = TypeVar("T", bound="Targeting")


@_attrs_define
class Targeting:
    """Simple univariate assays only observe changes in one value in an InferenceResult.
    [`Targeting`] is our way of selecting what this value is.

        Attributes:
            data_origin (DataOrigin): Specifies where the data this assay is [Targeting] is coming from.
                Currently, this only refers to which "topic" in Plateau.
            iopath (list['DataPath']): For Univariate assays, even though individual datums are not affecting each other's
                scores,
                we can still process Univariate assays on all specified fields.
    """

    data_origin: "DataOrigin"
    iopath: list["DataPath"]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data_origin = self.data_origin.to_dict()

        iopath = []
        for componentsschemas_data_batch_item_data in self.iopath:
            componentsschemas_data_batch_item = (
                componentsschemas_data_batch_item_data.to_dict()
            )
            iopath.append(componentsschemas_data_batch_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "data_origin": data_origin,
                "iopath": iopath,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.data_origin import DataOrigin
        from ..models.data_path import DataPath

        d = dict(src_dict)
        data_origin = DataOrigin.from_dict(d.pop("data_origin"))

        iopath = []
        _iopath = d.pop("iopath")
        for componentsschemas_data_batch_item_data in _iopath:
            componentsschemas_data_batch_item = DataPath.from_dict(
                componentsschemas_data_batch_item_data
            )

            iopath.append(componentsschemas_data_batch_item)

        targeting = cls(
            data_origin=data_origin,
            iopath=iopath,
        )

        targeting.additional_properties = d
        return targeting

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
