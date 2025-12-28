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
    from ..models.assays_run_interactive_baseline_body_baseline_type_1_static import (
        AssaysRunInteractiveBaselineBodyBaselineType1Static,
    )


T = TypeVar("T", bound="AssaysRunInteractiveBaselineBodyBaselineType1")


@_attrs_define
class AssaysRunInteractiveBaselineBodyBaselineType1:
    """
    Attributes:
        static (AssaysRunInteractiveBaselineBodyBaselineType1Static):  Result from summarizing one sample collection.
    """

    static: "AssaysRunInteractiveBaselineBodyBaselineType1Static"
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        static = self.static.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "static": static,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.assays_run_interactive_baseline_body_baseline_type_1_static import (
            AssaysRunInteractiveBaselineBodyBaselineType1Static,
        )

        d = dict(src_dict)
        static = AssaysRunInteractiveBaselineBodyBaselineType1Static.from_dict(
            d.pop("static")
        )

        assays_run_interactive_baseline_body_baseline_type_1 = cls(
            static=static,
        )

        assays_run_interactive_baseline_body_baseline_type_1.additional_properties = d
        return assays_run_interactive_baseline_body_baseline_type_1

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
