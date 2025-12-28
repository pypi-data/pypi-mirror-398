from collections.abc import Mapping
from typing import (
    Any,
    TypeVar,
    Union,
    cast,
)

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..models.auto_scale_config_type_2_type import AutoScaleConfigType2Type
from ..types import UNSET, Unset

T = TypeVar("T", bound="AutoScaleConfigType2")


@_attrs_define
class AutoScaleConfigType2:
    """
    Attributes:
        replica_max (int):
        replica_min (int):
        scale_down_queue_depth (float):
        scale_up_queue_depth (float):
        type_ (AutoScaleConfigType2Type):
        autoscaling_window (Union[None, Unset, int]):
    """

    replica_max: int
    replica_min: int
    scale_down_queue_depth: float
    scale_up_queue_depth: float
    type_: AutoScaleConfigType2Type
    autoscaling_window: Union[None, Unset, int] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        replica_max = self.replica_max

        replica_min = self.replica_min

        scale_down_queue_depth = self.scale_down_queue_depth

        scale_up_queue_depth = self.scale_up_queue_depth

        type_ = self.type_.value

        autoscaling_window: Union[None, Unset, int]
        if isinstance(self.autoscaling_window, Unset):
            autoscaling_window = UNSET
        else:
            autoscaling_window = self.autoscaling_window

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "replica_max": replica_max,
                "replica_min": replica_min,
                "scale_down_queue_depth": scale_down_queue_depth,
                "scale_up_queue_depth": scale_up_queue_depth,
                "type": type_,
            }
        )
        if autoscaling_window is not UNSET:
            field_dict["autoscaling_window"] = autoscaling_window

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        replica_max = d.pop("replica_max")

        replica_min = d.pop("replica_min")

        scale_down_queue_depth = d.pop("scale_down_queue_depth")

        scale_up_queue_depth = d.pop("scale_up_queue_depth")

        type_ = AutoScaleConfigType2Type(d.pop("type"))

        def _parse_autoscaling_window(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        autoscaling_window = _parse_autoscaling_window(
            d.pop("autoscaling_window", UNSET)
        )

        auto_scale_config_type_2 = cls(
            replica_max=replica_max,
            replica_min=replica_min,
            scale_down_queue_depth=scale_down_queue_depth,
            scale_up_queue_depth=scale_up_queue_depth,
            type_=type_,
            autoscaling_window=autoscaling_window,
        )

        auto_scale_config_type_2.additional_properties = d
        return auto_scale_config_type_2

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
