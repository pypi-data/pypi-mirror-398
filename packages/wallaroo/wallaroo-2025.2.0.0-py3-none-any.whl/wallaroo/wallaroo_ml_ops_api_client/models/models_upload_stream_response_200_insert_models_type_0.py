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
    from ..models.models_upload_stream_response_200_insert_models_type_0_returning_item import (
        ModelsUploadStreamResponse200InsertModelsType0ReturningItem,
    )


T = TypeVar("T", bound="ModelsUploadStreamResponse200InsertModelsType0")


@_attrs_define
class ModelsUploadStreamResponse200InsertModelsType0:
    """Response payload wrapper.

    Attributes:
        returning (list['ModelsUploadStreamResponse200InsertModelsType0ReturningItem']):  List of response details.
    """

    returning: list["ModelsUploadStreamResponse200InsertModelsType0ReturningItem"]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        returning = []
        for returning_item_data in self.returning:
            returning_item = returning_item_data.to_dict()
            returning.append(returning_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "returning": returning,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.models_upload_stream_response_200_insert_models_type_0_returning_item import (
            ModelsUploadStreamResponse200InsertModelsType0ReturningItem,
        )

        d = dict(src_dict)
        returning = []
        _returning = d.pop("returning")
        for returning_item_data in _returning:
            returning_item = (
                ModelsUploadStreamResponse200InsertModelsType0ReturningItem.from_dict(
                    returning_item_data
                )
            )

            returning.append(returning_item)

        models_upload_stream_response_200_insert_models_type_0 = cls(
            returning=returning,
        )

        models_upload_stream_response_200_insert_models_type_0.additional_properties = d
        return models_upload_stream_response_200_insert_models_type_0

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
