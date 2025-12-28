from collections.abc import Mapping
from typing import (
    TYPE_CHECKING,
    Any,
    TypeVar,
    Union,
)

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

if TYPE_CHECKING:
    from ..models.assays_get_assay_by_id_response_200_baseline_type_0_calculated_type_0 import (
        AssaysGetAssayByIdResponse200BaselineType0CalculatedType0,
    )
    from ..models.assays_get_assay_by_id_response_200_baseline_type_0_calculated_type_1 import (
        AssaysGetAssayByIdResponse200BaselineType0CalculatedType1,
    )
    from ..models.assays_get_assay_by_id_response_200_baseline_type_0_calculated_type_2 import (
        AssaysGetAssayByIdResponse200BaselineType0CalculatedType2,
    )


T = TypeVar("T", bound="AssaysGetAssayByIdResponse200BaselineType0")


@_attrs_define
class AssaysGetAssayByIdResponse200BaselineType0:
    """
    Attributes:
        calculated (Union['AssaysGetAssayByIdResponse200BaselineType0CalculatedType0',
            'AssaysGetAssayByIdResponse200BaselineType0CalculatedType1',
            'AssaysGetAssayByIdResponse200BaselineType0CalculatedType2']):
    """

    calculated: Union[
        "AssaysGetAssayByIdResponse200BaselineType0CalculatedType0",
        "AssaysGetAssayByIdResponse200BaselineType0CalculatedType1",
        "AssaysGetAssayByIdResponse200BaselineType0CalculatedType2",
    ]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.assays_get_assay_by_id_response_200_baseline_type_0_calculated_type_0 import (
            AssaysGetAssayByIdResponse200BaselineType0CalculatedType0,
        )
        from ..models.assays_get_assay_by_id_response_200_baseline_type_0_calculated_type_1 import (
            AssaysGetAssayByIdResponse200BaselineType0CalculatedType1,
        )

        calculated: dict[str, Any]
        if isinstance(
            self.calculated, AssaysGetAssayByIdResponse200BaselineType0CalculatedType0
        ):
            calculated = self.calculated.to_dict()
        elif isinstance(
            self.calculated, AssaysGetAssayByIdResponse200BaselineType0CalculatedType1
        ):
            calculated = self.calculated.to_dict()
        else:
            calculated = self.calculated.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "calculated": calculated,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.assays_get_assay_by_id_response_200_baseline_type_0_calculated_type_0 import (
            AssaysGetAssayByIdResponse200BaselineType0CalculatedType0,
        )
        from ..models.assays_get_assay_by_id_response_200_baseline_type_0_calculated_type_1 import (
            AssaysGetAssayByIdResponse200BaselineType0CalculatedType1,
        )
        from ..models.assays_get_assay_by_id_response_200_baseline_type_0_calculated_type_2 import (
            AssaysGetAssayByIdResponse200BaselineType0CalculatedType2,
        )

        d = dict(src_dict)

        def _parse_calculated(
            data: object,
        ) -> Union[
            "AssaysGetAssayByIdResponse200BaselineType0CalculatedType0",
            "AssaysGetAssayByIdResponse200BaselineType0CalculatedType1",
            "AssaysGetAssayByIdResponse200BaselineType0CalculatedType2",
        ]:
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                calculated_type_0 = (
                    AssaysGetAssayByIdResponse200BaselineType0CalculatedType0.from_dict(
                        data
                    )
                )

                return calculated_type_0
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                calculated_type_1 = (
                    AssaysGetAssayByIdResponse200BaselineType0CalculatedType1.from_dict(
                        data
                    )
                )

                return calculated_type_1
            except:  # noqa: E722
                pass
            if not isinstance(data, dict):
                raise TypeError()
            calculated_type_2 = (
                AssaysGetAssayByIdResponse200BaselineType0CalculatedType2.from_dict(
                    data
                )
            )

            return calculated_type_2

        calculated = _parse_calculated(d.pop("calculated"))

        assays_get_assay_by_id_response_200_baseline_type_0 = cls(
            calculated=calculated,
        )

        assays_get_assay_by_id_response_200_baseline_type_0.additional_properties = d
        return assays_get_assay_by_id_response_200_baseline_type_0

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
