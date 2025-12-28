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
    from ..models.network_service_request_json import NetworkServiceRequestJson


T = TypeVar("T", bound="NetworkServiceRequest")


@_attrs_define
class NetworkServiceRequest:
    """
    Attributes:
        json (NetworkServiceRequestJson):
        name (str):
        orch_id (UUID):
        workspace_id (int):
        debug (Union[None, Unset, bool]):
    """

    json: "NetworkServiceRequestJson"
    name: str
    orch_id: UUID
    workspace_id: int
    debug: Union[None, Unset, bool] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        json = self.json.to_dict()

        name = self.name

        orch_id = str(self.orch_id)

        workspace_id = self.workspace_id

        debug: Union[None, Unset, bool]
        if isinstance(self.debug, Unset):
            debug = UNSET
        else:
            debug = self.debug

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "json": json,
                "name": name,
                "orch_id": orch_id,
                "workspace_id": workspace_id,
            }
        )
        if debug is not UNSET:
            field_dict["debug"] = debug

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.network_service_request_json import NetworkServiceRequestJson

        d = dict(src_dict)
        json = NetworkServiceRequestJson.from_dict(d.pop("json"))

        name = d.pop("name")

        orch_id = UUID(d.pop("orch_id"))

        workspace_id = d.pop("workspace_id")

        def _parse_debug(data: object) -> Union[None, Unset, bool]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, bool], data)

        debug = _parse_debug(d.pop("debug", UNSET))

        network_service_request = cls(
            json=json,
            name=name,
            orch_id=orch_id,
            workspace_id=workspace_id,
            debug=debug,
        )

        network_service_request.additional_properties = d
        return network_service_request

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
