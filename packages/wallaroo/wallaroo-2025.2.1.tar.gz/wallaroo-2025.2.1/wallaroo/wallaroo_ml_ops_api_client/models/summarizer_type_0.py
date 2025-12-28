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
    from ..models.univariate_continuous import UnivariateContinuous


T = TypeVar("T", bound="SummarizerType0")


@_attrs_define
class SummarizerType0:
    """
    Attributes:
        univariate_continuous (UnivariateContinuous): Defines the summarizer/test we want to conduct
    """

    univariate_continuous: "UnivariateContinuous"
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        univariate_continuous = self.univariate_continuous.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "UnivariateContinuous": univariate_continuous,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.univariate_continuous import UnivariateContinuous

        d = dict(src_dict)
        univariate_continuous = UnivariateContinuous.from_dict(
            d.pop("UnivariateContinuous")
        )

        summarizer_type_0 = cls(
            univariate_continuous=univariate_continuous,
        )

        summarizer_type_0.additional_properties = d
        return summarizer_type_0

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
