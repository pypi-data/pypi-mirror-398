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
    from ..models.completion_config_chat_template_kwargs_type_0 import (
        CompletionConfigChatTemplateKwargsType0,
    )
    from ..models.completion_config_documents_type_0_item import (
        CompletionConfigDocumentsType0Item,
    )
    from ..models.completion_config_logit_bias_type_0 import (
        CompletionConfigLogitBiasType0,
    )


T = TypeVar("T", bound="CompletionConfig")


@_attrs_define
class CompletionConfig:
    """
    Attributes:
        add_generation_prompt (Union[None, Unset, bool]):
        add_special_tokens (Union[None, Unset, bool]):
        best_of (Union[None, Unset, int]):
        chat_template (Union[None, Unset, str]):
        chat_template_kwargs (Union['CompletionConfigChatTemplateKwargsType0', None, Unset]):
        documents (Union[None, Unset, list['CompletionConfigDocumentsType0Item']]):
        echo (Union[None, Unset, bool]):
        frequency_penalty (Union[None, Unset, float]):
        guided_choice (Union[None, Unset, list[str]]):
        guided_decoding_backend (Union[None, Unset, str]):
        guided_grammar (Union[None, Unset, str]):
        guided_json (Union[Unset, Any]):
        guided_regex (Union[None, Unset, str]):
        guided_whitespace_pattern (Union[None, Unset, str]):
        logit_bias (Union['CompletionConfigLogitBiasType0', None, Unset]):
        logprobs (Union[None, Unset, int]):
        max_tokens (Union[None, Unset, int]):
        n (Union[None, Unset, int]):
        presence_penalty (Union[None, Unset, float]):
        seed (Union[None, Unset, int]):
        stop (Union[None, Unset, list[str]]):
        suffix (Union[None, Unset, str]):
        temperature (Union[None, Unset, float]):
        top_p (Union[None, Unset, float]):
        user (Union[None, Unset, str]):
    """

    add_generation_prompt: Union[None, Unset, bool] = UNSET
    add_special_tokens: Union[None, Unset, bool] = UNSET
    best_of: Union[None, Unset, int] = UNSET
    chat_template: Union[None, Unset, str] = UNSET
    chat_template_kwargs: Union[
        "CompletionConfigChatTemplateKwargsType0", None, Unset
    ] = UNSET
    documents: Union[None, Unset, list["CompletionConfigDocumentsType0Item"]] = UNSET
    echo: Union[None, Unset, bool] = UNSET
    frequency_penalty: Union[None, Unset, float] = UNSET
    guided_choice: Union[None, Unset, list[str]] = UNSET
    guided_decoding_backend: Union[None, Unset, str] = UNSET
    guided_grammar: Union[None, Unset, str] = UNSET
    guided_json: Union[Unset, Any] = UNSET
    guided_regex: Union[None, Unset, str] = UNSET
    guided_whitespace_pattern: Union[None, Unset, str] = UNSET
    logit_bias: Union["CompletionConfigLogitBiasType0", None, Unset] = UNSET
    logprobs: Union[None, Unset, int] = UNSET
    max_tokens: Union[None, Unset, int] = UNSET
    n: Union[None, Unset, int] = UNSET
    presence_penalty: Union[None, Unset, float] = UNSET
    seed: Union[None, Unset, int] = UNSET
    stop: Union[None, Unset, list[str]] = UNSET
    suffix: Union[None, Unset, str] = UNSET
    temperature: Union[None, Unset, float] = UNSET
    top_p: Union[None, Unset, float] = UNSET
    user: Union[None, Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.completion_config_chat_template_kwargs_type_0 import (
            CompletionConfigChatTemplateKwargsType0,
        )
        from ..models.completion_config_logit_bias_type_0 import (
            CompletionConfigLogitBiasType0,
        )

        add_generation_prompt: Union[None, Unset, bool]
        if isinstance(self.add_generation_prompt, Unset):
            add_generation_prompt = UNSET
        else:
            add_generation_prompt = self.add_generation_prompt

        add_special_tokens: Union[None, Unset, bool]
        if isinstance(self.add_special_tokens, Unset):
            add_special_tokens = UNSET
        else:
            add_special_tokens = self.add_special_tokens

        best_of: Union[None, Unset, int]
        if isinstance(self.best_of, Unset):
            best_of = UNSET
        else:
            best_of = self.best_of

        chat_template: Union[None, Unset, str]
        if isinstance(self.chat_template, Unset):
            chat_template = UNSET
        else:
            chat_template = self.chat_template

        chat_template_kwargs: Union[None, Unset, dict[str, Any]]
        if isinstance(self.chat_template_kwargs, Unset):
            chat_template_kwargs = UNSET
        elif isinstance(
            self.chat_template_kwargs, CompletionConfigChatTemplateKwargsType0
        ):
            chat_template_kwargs = self.chat_template_kwargs.to_dict()
        else:
            chat_template_kwargs = self.chat_template_kwargs

        documents: Union[None, Unset, list[dict[str, Any]]]
        if isinstance(self.documents, Unset):
            documents = UNSET
        elif isinstance(self.documents, list):
            documents = []
            for documents_type_0_item_data in self.documents:
                documents_type_0_item = documents_type_0_item_data.to_dict()
                documents.append(documents_type_0_item)

        else:
            documents = self.documents

        echo: Union[None, Unset, bool]
        if isinstance(self.echo, Unset):
            echo = UNSET
        else:
            echo = self.echo

        frequency_penalty: Union[None, Unset, float]
        if isinstance(self.frequency_penalty, Unset):
            frequency_penalty = UNSET
        else:
            frequency_penalty = self.frequency_penalty

        guided_choice: Union[None, Unset, list[str]]
        if isinstance(self.guided_choice, Unset):
            guided_choice = UNSET
        elif isinstance(self.guided_choice, list):
            guided_choice = self.guided_choice

        else:
            guided_choice = self.guided_choice

        guided_decoding_backend: Union[None, Unset, str]
        if isinstance(self.guided_decoding_backend, Unset):
            guided_decoding_backend = UNSET
        else:
            guided_decoding_backend = self.guided_decoding_backend

        guided_grammar: Union[None, Unset, str]
        if isinstance(self.guided_grammar, Unset):
            guided_grammar = UNSET
        else:
            guided_grammar = self.guided_grammar

        guided_json = self.guided_json

        guided_regex: Union[None, Unset, str]
        if isinstance(self.guided_regex, Unset):
            guided_regex = UNSET
        else:
            guided_regex = self.guided_regex

        guided_whitespace_pattern: Union[None, Unset, str]
        if isinstance(self.guided_whitespace_pattern, Unset):
            guided_whitespace_pattern = UNSET
        else:
            guided_whitespace_pattern = self.guided_whitespace_pattern

        logit_bias: Union[None, Unset, dict[str, Any]]
        if isinstance(self.logit_bias, Unset):
            logit_bias = UNSET
        elif isinstance(self.logit_bias, CompletionConfigLogitBiasType0):
            logit_bias = self.logit_bias.to_dict()
        else:
            logit_bias = self.logit_bias

        logprobs: Union[None, Unset, int]
        if isinstance(self.logprobs, Unset):
            logprobs = UNSET
        else:
            logprobs = self.logprobs

        max_tokens: Union[None, Unset, int]
        if isinstance(self.max_tokens, Unset):
            max_tokens = UNSET
        else:
            max_tokens = self.max_tokens

        n: Union[None, Unset, int]
        if isinstance(self.n, Unset):
            n = UNSET
        else:
            n = self.n

        presence_penalty: Union[None, Unset, float]
        if isinstance(self.presence_penalty, Unset):
            presence_penalty = UNSET
        else:
            presence_penalty = self.presence_penalty

        seed: Union[None, Unset, int]
        if isinstance(self.seed, Unset):
            seed = UNSET
        else:
            seed = self.seed

        stop: Union[None, Unset, list[str]]
        if isinstance(self.stop, Unset):
            stop = UNSET
        elif isinstance(self.stop, list):
            stop = self.stop

        else:
            stop = self.stop

        suffix: Union[None, Unset, str]
        if isinstance(self.suffix, Unset):
            suffix = UNSET
        else:
            suffix = self.suffix

        temperature: Union[None, Unset, float]
        if isinstance(self.temperature, Unset):
            temperature = UNSET
        else:
            temperature = self.temperature

        top_p: Union[None, Unset, float]
        if isinstance(self.top_p, Unset):
            top_p = UNSET
        else:
            top_p = self.top_p

        user: Union[None, Unset, str]
        if isinstance(self.user, Unset):
            user = UNSET
        else:
            user = self.user

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if add_generation_prompt is not UNSET:
            field_dict["add_generation_prompt"] = add_generation_prompt
        if add_special_tokens is not UNSET:
            field_dict["add_special_tokens"] = add_special_tokens
        if best_of is not UNSET:
            field_dict["best_of"] = best_of
        if chat_template is not UNSET:
            field_dict["chat_template"] = chat_template
        if chat_template_kwargs is not UNSET:
            field_dict["chat_template_kwargs"] = chat_template_kwargs
        if documents is not UNSET:
            field_dict["documents"] = documents
        if echo is not UNSET:
            field_dict["echo"] = echo
        if frequency_penalty is not UNSET:
            field_dict["frequency_penalty"] = frequency_penalty
        if guided_choice is not UNSET:
            field_dict["guided_choice"] = guided_choice
        if guided_decoding_backend is not UNSET:
            field_dict["guided_decoding_backend"] = guided_decoding_backend
        if guided_grammar is not UNSET:
            field_dict["guided_grammar"] = guided_grammar
        if guided_json is not UNSET:
            field_dict["guided_json"] = guided_json
        if guided_regex is not UNSET:
            field_dict["guided_regex"] = guided_regex
        if guided_whitespace_pattern is not UNSET:
            field_dict["guided_whitespace_pattern"] = guided_whitespace_pattern
        if logit_bias is not UNSET:
            field_dict["logit_bias"] = logit_bias
        if logprobs is not UNSET:
            field_dict["logprobs"] = logprobs
        if max_tokens is not UNSET:
            field_dict["max_tokens"] = max_tokens
        if n is not UNSET:
            field_dict["n"] = n
        if presence_penalty is not UNSET:
            field_dict["presence_penalty"] = presence_penalty
        if seed is not UNSET:
            field_dict["seed"] = seed
        if stop is not UNSET:
            field_dict["stop"] = stop
        if suffix is not UNSET:
            field_dict["suffix"] = suffix
        if temperature is not UNSET:
            field_dict["temperature"] = temperature
        if top_p is not UNSET:
            field_dict["top_p"] = top_p
        if user is not UNSET:
            field_dict["user"] = user

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.completion_config_chat_template_kwargs_type_0 import (
            CompletionConfigChatTemplateKwargsType0,
        )
        from ..models.completion_config_documents_type_0_item import (
            CompletionConfigDocumentsType0Item,
        )
        from ..models.completion_config_logit_bias_type_0 import (
            CompletionConfigLogitBiasType0,
        )

        d = dict(src_dict)

        def _parse_add_generation_prompt(data: object) -> Union[None, Unset, bool]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, bool], data)

        add_generation_prompt = _parse_add_generation_prompt(
            d.pop("add_generation_prompt", UNSET)
        )

        def _parse_add_special_tokens(data: object) -> Union[None, Unset, bool]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, bool], data)

        add_special_tokens = _parse_add_special_tokens(
            d.pop("add_special_tokens", UNSET)
        )

        def _parse_best_of(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        best_of = _parse_best_of(d.pop("best_of", UNSET))

        def _parse_chat_template(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        chat_template = _parse_chat_template(d.pop("chat_template", UNSET))

        def _parse_chat_template_kwargs(
            data: object,
        ) -> Union["CompletionConfigChatTemplateKwargsType0", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                chat_template_kwargs_type_0 = (
                    CompletionConfigChatTemplateKwargsType0.from_dict(data)
                )

                return chat_template_kwargs_type_0
            except:  # noqa: E722
                pass
            return cast(
                Union["CompletionConfigChatTemplateKwargsType0", None, Unset], data
            )

        chat_template_kwargs = _parse_chat_template_kwargs(
            d.pop("chat_template_kwargs", UNSET)
        )

        def _parse_documents(
            data: object,
        ) -> Union[None, Unset, list["CompletionConfigDocumentsType0Item"]]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                documents_type_0 = []
                _documents_type_0 = data
                for documents_type_0_item_data in _documents_type_0:
                    documents_type_0_item = (
                        CompletionConfigDocumentsType0Item.from_dict(
                            documents_type_0_item_data
                        )
                    )

                    documents_type_0.append(documents_type_0_item)

                return documents_type_0
            except:  # noqa: E722
                pass
            return cast(
                Union[None, Unset, list["CompletionConfigDocumentsType0Item"]], data
            )

        documents = _parse_documents(d.pop("documents", UNSET))

        def _parse_echo(data: object) -> Union[None, Unset, bool]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, bool], data)

        echo = _parse_echo(d.pop("echo", UNSET))

        def _parse_frequency_penalty(data: object) -> Union[None, Unset, float]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, float], data)

        frequency_penalty = _parse_frequency_penalty(d.pop("frequency_penalty", UNSET))

        def _parse_guided_choice(data: object) -> Union[None, Unset, list[str]]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                guided_choice_type_0 = cast(list[str], data)

                return guided_choice_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, list[str]], data)

        guided_choice = _parse_guided_choice(d.pop("guided_choice", UNSET))

        def _parse_guided_decoding_backend(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        guided_decoding_backend = _parse_guided_decoding_backend(
            d.pop("guided_decoding_backend", UNSET)
        )

        def _parse_guided_grammar(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        guided_grammar = _parse_guided_grammar(d.pop("guided_grammar", UNSET))

        guided_json = d.pop("guided_json", UNSET)

        def _parse_guided_regex(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        guided_regex = _parse_guided_regex(d.pop("guided_regex", UNSET))

        def _parse_guided_whitespace_pattern(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        guided_whitespace_pattern = _parse_guided_whitespace_pattern(
            d.pop("guided_whitespace_pattern", UNSET)
        )

        def _parse_logit_bias(
            data: object,
        ) -> Union["CompletionConfigLogitBiasType0", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                logit_bias_type_0 = CompletionConfigLogitBiasType0.from_dict(data)

                return logit_bias_type_0
            except:  # noqa: E722
                pass
            return cast(Union["CompletionConfigLogitBiasType0", None, Unset], data)

        logit_bias = _parse_logit_bias(d.pop("logit_bias", UNSET))

        def _parse_logprobs(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        logprobs = _parse_logprobs(d.pop("logprobs", UNSET))

        def _parse_max_tokens(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        max_tokens = _parse_max_tokens(d.pop("max_tokens", UNSET))

        def _parse_n(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        n = _parse_n(d.pop("n", UNSET))

        def _parse_presence_penalty(data: object) -> Union[None, Unset, float]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, float], data)

        presence_penalty = _parse_presence_penalty(d.pop("presence_penalty", UNSET))

        def _parse_seed(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        seed = _parse_seed(d.pop("seed", UNSET))

        def _parse_stop(data: object) -> Union[None, Unset, list[str]]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                stop_type_0 = cast(list[str], data)

                return stop_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, list[str]], data)

        stop = _parse_stop(d.pop("stop", UNSET))

        def _parse_suffix(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        suffix = _parse_suffix(d.pop("suffix", UNSET))

        def _parse_temperature(data: object) -> Union[None, Unset, float]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, float], data)

        temperature = _parse_temperature(d.pop("temperature", UNSET))

        def _parse_top_p(data: object) -> Union[None, Unset, float]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, float], data)

        top_p = _parse_top_p(d.pop("top_p", UNSET))

        def _parse_user(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        user = _parse_user(d.pop("user", UNSET))

        completion_config = cls(
            add_generation_prompt=add_generation_prompt,
            add_special_tokens=add_special_tokens,
            best_of=best_of,
            chat_template=chat_template,
            chat_template_kwargs=chat_template_kwargs,
            documents=documents,
            echo=echo,
            frequency_penalty=frequency_penalty,
            guided_choice=guided_choice,
            guided_decoding_backend=guided_decoding_backend,
            guided_grammar=guided_grammar,
            guided_json=guided_json,
            guided_regex=guided_regex,
            guided_whitespace_pattern=guided_whitespace_pattern,
            logit_bias=logit_bias,
            logprobs=logprobs,
            max_tokens=max_tokens,
            n=n,
            presence_penalty=presence_penalty,
            seed=seed,
            stop=stop,
            suffix=suffix,
            temperature=temperature,
            top_p=top_p,
            user=user,
        )

        completion_config.additional_properties = d
        return completion_config

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
