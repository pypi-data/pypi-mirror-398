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
    from ..models.chat_completion_config import ChatCompletionConfig
    from ..models.completion_config import CompletionConfig


T = TypeVar("T", bound="OpenAiConfig")


@_attrs_define
class OpenAiConfig:
    """
    Attributes:
        enabled (bool):
        chat_completion_config (Union['ChatCompletionConfig', None, Unset]):
        completion_config (Union['CompletionConfig', None, Unset]):
    """

    enabled: bool
    chat_completion_config: Union["ChatCompletionConfig", None, Unset] = UNSET
    completion_config: Union["CompletionConfig", None, Unset] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.chat_completion_config import ChatCompletionConfig
        from ..models.completion_config import CompletionConfig

        enabled = self.enabled

        chat_completion_config: Union[None, Unset, dict[str, Any]]
        if isinstance(self.chat_completion_config, Unset):
            chat_completion_config = UNSET
        elif isinstance(self.chat_completion_config, ChatCompletionConfig):
            chat_completion_config = self.chat_completion_config.to_dict()
        else:
            chat_completion_config = self.chat_completion_config

        completion_config: Union[None, Unset, dict[str, Any]]
        if isinstance(self.completion_config, Unset):
            completion_config = UNSET
        elif isinstance(self.completion_config, CompletionConfig):
            completion_config = self.completion_config.to_dict()
        else:
            completion_config = self.completion_config

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "enabled": enabled,
            }
        )
        if chat_completion_config is not UNSET:
            field_dict["chat_completion_config"] = chat_completion_config
        if completion_config is not UNSET:
            field_dict["completion_config"] = completion_config

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.chat_completion_config import ChatCompletionConfig
        from ..models.completion_config import CompletionConfig

        d = dict(src_dict)
        enabled = d.pop("enabled")

        def _parse_chat_completion_config(
            data: object,
        ) -> Union["ChatCompletionConfig", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                chat_completion_config_type_1 = ChatCompletionConfig.from_dict(data)

                return chat_completion_config_type_1
            except:  # noqa: E722
                pass
            return cast(Union["ChatCompletionConfig", None, Unset], data)

        chat_completion_config = _parse_chat_completion_config(
            d.pop("chat_completion_config", UNSET)
        )

        def _parse_completion_config(
            data: object,
        ) -> Union["CompletionConfig", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                completion_config_type_1 = CompletionConfig.from_dict(data)

                return completion_config_type_1
            except:  # noqa: E722
                pass
            return cast(Union["CompletionConfig", None, Unset], data)

        completion_config = _parse_completion_config(d.pop("completion_config", UNSET))

        open_ai_config = cls(
            enabled=enabled,
            chat_completion_config=chat_completion_config,
            completion_config=completion_config,
        )

        open_ai_config.additional_properties = d
        return open_ai_config

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
