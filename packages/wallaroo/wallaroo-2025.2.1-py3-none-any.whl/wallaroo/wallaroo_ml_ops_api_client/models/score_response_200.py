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

if TYPE_CHECKING:
    from ..models.score_data import ScoreData


T = TypeVar("T", bound="ScoreResponse200")


@_attrs_define
class ScoreResponse200:
    """ """

    additional_properties: dict[str, Union["ScoreData", str]] = _attrs_field(
        init=False, factory=dict
    )

    def to_dict(self) -> dict[str, Any]:
        from ..models.score_data import ScoreData

        field_dict: dict[str, Any] = {}
        for prop_name, prop in self.additional_properties.items():
            if isinstance(prop, ScoreData):
                field_dict[prop_name] = prop.to_dict()
            else:
                field_dict[prop_name] = prop

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.score_data import ScoreData

        d = dict(src_dict)
        score_response_200 = cls()

        additional_properties = {}
        for prop_name, prop_dict in d.items():

            def _parse_additional_property(data: object) -> Union["ScoreData", str]:
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    componentsschemas_score_type_0 = ScoreData.from_dict(data)

                    return componentsschemas_score_type_0
                except:  # noqa: E722
                    pass
                return cast(Union["ScoreData", str], data)

            additional_property = _parse_additional_property(prop_dict)

            additional_properties[prop_name] = additional_property

        score_response_200.additional_properties = additional_properties
        return score_response_200

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Union["ScoreData", str]:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Union["ScoreData", str]) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
