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
    from ..models.models_upload_stream_response_200_insert_models_type_0 import (
        ModelsUploadStreamResponse200InsertModelsType0,
    )


T = TypeVar("T", bound="ModelsUploadStreamResponse200")


@_attrs_define
class ModelsUploadStreamResponse200:
    """Successful response to model upload.

    Attributes:
        insert_models (Union['ModelsUploadStreamResponse200InsertModelsType0', None, Unset]):  Response payload wrapper.
    """

    insert_models: Union[
        "ModelsUploadStreamResponse200InsertModelsType0", None, Unset
    ] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.models_upload_stream_response_200_insert_models_type_0 import (
            ModelsUploadStreamResponse200InsertModelsType0,
        )

        insert_models: Union[None, Unset, dict[str, Any]]
        if isinstance(self.insert_models, Unset):
            insert_models = UNSET
        elif isinstance(
            self.insert_models, ModelsUploadStreamResponse200InsertModelsType0
        ):
            insert_models = self.insert_models.to_dict()
        else:
            insert_models = self.insert_models

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if insert_models is not UNSET:
            field_dict["insert_models"] = insert_models

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.models_upload_stream_response_200_insert_models_type_0 import (
            ModelsUploadStreamResponse200InsertModelsType0,
        )

        d = dict(src_dict)

        def _parse_insert_models(
            data: object,
        ) -> Union["ModelsUploadStreamResponse200InsertModelsType0", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                insert_models_type_0 = (
                    ModelsUploadStreamResponse200InsertModelsType0.from_dict(data)
                )

                return insert_models_type_0
            except:  # noqa: E722
                pass
            return cast(
                Union["ModelsUploadStreamResponse200InsertModelsType0", None, Unset],
                data,
            )

        insert_models = _parse_insert_models(d.pop("insert_models", UNSET))

        models_upload_stream_response_200 = cls(
            insert_models=insert_models,
        )

        models_upload_stream_response_200.additional_properties = d
        return models_upload_stream_response_200

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
