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

from ..models.bin_mode_type_0 import BinModeType0

if TYPE_CHECKING:
    from ..models.bin_mode_type_1 import BinModeType1
    from ..models.bin_mode_type_2 import BinModeType2
    from ..models.bin_mode_type_3 import BinModeType3
    from ..models.bin_mode_type_4 import BinModeType4


T = TypeVar("T", bound="Bins")


@_attrs_define
class Bins:
    """Bins are ranges for a dataset, ranging from [`std::f64::NEG_INFINITY`] to [`std::f64::INFINITY`].
    A single bin is described by two values, the left edge (>=) and the right edge

        Attributes:
            edges (list[float]): A Vec of the right-edges of a set of histogram bins.
                The right-edge may be [`std::f64::INFINITY`]
            labels (list[str]):
            mode (Union['BinModeType1', 'BinModeType2', 'BinModeType3', 'BinModeType4', BinModeType0]):
    """

    edges: list[float]
    labels: list[str]
    mode: Union[
        "BinModeType1", "BinModeType2", "BinModeType3", "BinModeType4", BinModeType0
    ]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.bin_mode_type_1 import BinModeType1
        from ..models.bin_mode_type_2 import BinModeType2
        from ..models.bin_mode_type_3 import BinModeType3

        edges = self.edges

        labels = self.labels

        mode: Union[dict[str, Any], str]
        if isinstance(self.mode, BinModeType0):
            mode = self.mode.value
        elif isinstance(self.mode, BinModeType1):
            mode = self.mode.to_dict()
        elif isinstance(self.mode, BinModeType2):
            mode = self.mode.to_dict()
        elif isinstance(self.mode, BinModeType3):
            mode = self.mode.to_dict()
        else:
            mode = self.mode.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "edges": edges,
                "labels": labels,
                "mode": mode,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.bin_mode_type_1 import BinModeType1
        from ..models.bin_mode_type_2 import BinModeType2
        from ..models.bin_mode_type_3 import BinModeType3
        from ..models.bin_mode_type_4 import BinModeType4

        d = dict(src_dict)
        edges = cast(list[float], d.pop("edges"))

        labels = cast(list[str], d.pop("labels"))

        def _parse_mode(
            data: object,
        ) -> Union[
            "BinModeType1", "BinModeType2", "BinModeType3", "BinModeType4", BinModeType0
        ]:
            try:
                if not isinstance(data, str):
                    raise TypeError()
                componentsschemas_bin_mode_type_0 = BinModeType0(data)

                return componentsschemas_bin_mode_type_0
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_bin_mode_type_1 = BinModeType1.from_dict(data)

                return componentsschemas_bin_mode_type_1
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_bin_mode_type_2 = BinModeType2.from_dict(data)

                return componentsschemas_bin_mode_type_2
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_bin_mode_type_3 = BinModeType3.from_dict(data)

                return componentsschemas_bin_mode_type_3
            except:  # noqa: E722
                pass
            if not isinstance(data, dict):
                raise TypeError()
            componentsschemas_bin_mode_type_4 = BinModeType4.from_dict(data)

            return componentsschemas_bin_mode_type_4

        mode = _parse_mode(d.pop("mode"))

        bins = cls(
            edges=edges,
            labels=labels,
            mode=mode,
        )

        bins.additional_properties = d
        return bins

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
