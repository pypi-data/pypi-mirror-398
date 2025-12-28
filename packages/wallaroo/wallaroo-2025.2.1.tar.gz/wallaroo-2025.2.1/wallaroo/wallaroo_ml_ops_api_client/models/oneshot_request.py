from collections.abc import Mapping
from typing import (
    TYPE_CHECKING,
    Any,
    TypeVar,
    Union,
    cast,
)
from uuid import UUID

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.oneshot_request_json import OneshotRequestJson


T = TypeVar("T", bound="OneshotRequest")


@_attrs_define
class OneshotRequest:
    """
    Attributes:
        json (OneshotRequestJson):
        orch_id (UUID):
        workspace_id (int):
        debug (Union[None, Unset, bool]):
        name (Union[None, Unset, str]):
        timeout (Union[None, Unset, int]):
    """

    json: "OneshotRequestJson"
    orch_id: UUID
    workspace_id: int
    debug: Union[None, Unset, bool] = UNSET
    name: Union[None, Unset, str] = UNSET
    timeout: Union[None, Unset, int] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        json = self.json.to_dict()

        orch_id = str(self.orch_id)

        workspace_id = self.workspace_id

        debug: Union[None, Unset, bool]
        if isinstance(self.debug, Unset):
            debug = UNSET
        else:
            debug = self.debug

        name: Union[None, Unset, str]
        if isinstance(self.name, Unset):
            name = UNSET
        else:
            name = self.name

        timeout: Union[None, Unset, int]
        if isinstance(self.timeout, Unset):
            timeout = UNSET
        else:
            timeout = self.timeout

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "json": json,
                "orch_id": orch_id,
                "workspace_id": workspace_id,
            }
        )
        if debug is not UNSET:
            field_dict["debug"] = debug
        if name is not UNSET:
            field_dict["name"] = name
        if timeout is not UNSET:
            field_dict["timeout"] = timeout

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.oneshot_request_json import OneshotRequestJson

        d = dict(src_dict)
        json = OneshotRequestJson.from_dict(d.pop("json"))

        orch_id = UUID(d.pop("orch_id"))

        workspace_id = d.pop("workspace_id")

        def _parse_debug(data: object) -> Union[None, Unset, bool]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, bool], data)

        debug = _parse_debug(d.pop("debug", UNSET))

        def _parse_name(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        name = _parse_name(d.pop("name", UNSET))

        def _parse_timeout(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        timeout = _parse_timeout(d.pop("timeout", UNSET))

        oneshot_request = cls(
            json=json,
            orch_id=orch_id,
            workspace_id=workspace_id,
            debug=debug,
            name=name,
            timeout=timeout,
        )

        oneshot_request.additional_properties = d
        return oneshot_request

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
