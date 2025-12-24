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
    from ..models.v1_model_get_config_response_200_model_config_type_0 import (
        V1ModelGetConfigResponse200ModelConfigType0,
    )


T = TypeVar("T", bound="V1ModelGetConfigResponse200")


@_attrs_define
class V1ModelGetConfigResponse200:
    """Response body of /models/get_config_by_id

    Attributes:
        model_config (Union['V1ModelGetConfigResponse200ModelConfigType0', None, Unset]):  An optional Model
            Configuration
    """

    model_config: Union["V1ModelGetConfigResponse200ModelConfigType0", None, Unset] = (
        UNSET
    )
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.v1_model_get_config_response_200_model_config_type_0 import (
            V1ModelGetConfigResponse200ModelConfigType0,
        )

        model_config: Union[None, Unset, dict[str, Any]]
        if isinstance(self.model_config, Unset):
            model_config = UNSET
        elif isinstance(self.model_config, V1ModelGetConfigResponse200ModelConfigType0):
            model_config = self.model_config.to_dict()
        else:
            model_config = self.model_config

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if model_config is not UNSET:
            field_dict["model_config"] = model_config

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.v1_model_get_config_response_200_model_config_type_0 import (
            V1ModelGetConfigResponse200ModelConfigType0,
        )

        d = dict(src_dict)

        def _parse_model_config(
            data: object,
        ) -> Union["V1ModelGetConfigResponse200ModelConfigType0", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                model_config_type_0 = (
                    V1ModelGetConfigResponse200ModelConfigType0.from_dict(data)
                )

                return model_config_type_0
            except:  # noqa: E722
                pass
            return cast(
                Union["V1ModelGetConfigResponse200ModelConfigType0", None, Unset], data
            )

        model_config = _parse_model_config(d.pop("model_config", UNSET))

        v1_model_get_config_response_200 = cls(
            model_config=model_config,
        )

        v1_model_get_config_response_200.additional_properties = d
        return v1_model_get_config_response_200

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
