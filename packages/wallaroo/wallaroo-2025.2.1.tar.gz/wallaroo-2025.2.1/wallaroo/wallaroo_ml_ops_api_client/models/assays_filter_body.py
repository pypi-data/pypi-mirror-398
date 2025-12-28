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

from ..models.assays_filter_body_sort_by import AssaysFilterBodySortBy
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.assays_filter_body_drift_window_type_0 import (
        AssaysFilterBodyDriftWindowType0,
    )


T = TypeVar("T", bound="AssaysFilterBody")


@_attrs_define
class AssaysFilterBody:
    """
    Attributes:
        workspace_id (int):
        pipeline_id (int):
        sort_by (AssaysFilterBodySortBy):
        name (Union[None, Unset, str]):
        active (Union[None, Unset, bool]):
        drift_window (Union['AssaysFilterBodyDriftWindowType0', None, Unset]):
        locations (Union[None, Unset, list[str]]):
    """

    workspace_id: int
    pipeline_id: int
    sort_by: AssaysFilterBodySortBy
    name: Union[None, Unset, str] = UNSET
    active: Union[None, Unset, bool] = UNSET
    drift_window: Union["AssaysFilterBodyDriftWindowType0", None, Unset] = UNSET
    locations: Union[None, Unset, list[str]] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.assays_filter_body_drift_window_type_0 import (
            AssaysFilterBodyDriftWindowType0,
        )

        workspace_id = self.workspace_id

        pipeline_id = self.pipeline_id

        sort_by = self.sort_by.value

        name: Union[None, Unset, str]
        if isinstance(self.name, Unset):
            name = UNSET
        else:
            name = self.name

        active: Union[None, Unset, bool]
        if isinstance(self.active, Unset):
            active = UNSET
        else:
            active = self.active

        drift_window: Union[None, Unset, dict[str, Any]]
        if isinstance(self.drift_window, Unset):
            drift_window = UNSET
        elif isinstance(self.drift_window, AssaysFilterBodyDriftWindowType0):
            drift_window = self.drift_window.to_dict()
        else:
            drift_window = self.drift_window

        locations: Union[None, Unset, list[str]]
        if isinstance(self.locations, Unset):
            locations = UNSET
        elif isinstance(self.locations, list):
            locations = self.locations

        else:
            locations = self.locations

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "workspace_id": workspace_id,
                "pipeline_id": pipeline_id,
                "sort_by": sort_by,
            }
        )
        if name is not UNSET:
            field_dict["name"] = name
        if active is not UNSET:
            field_dict["active"] = active
        if drift_window is not UNSET:
            field_dict["drift_window"] = drift_window
        if locations is not UNSET:
            field_dict["locations"] = locations

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.assays_filter_body_drift_window_type_0 import (
            AssaysFilterBodyDriftWindowType0,
        )

        d = dict(src_dict)
        workspace_id = d.pop("workspace_id")

        pipeline_id = d.pop("pipeline_id")

        sort_by = AssaysFilterBodySortBy(d.pop("sort_by"))

        def _parse_name(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        name = _parse_name(d.pop("name", UNSET))

        def _parse_active(data: object) -> Union[None, Unset, bool]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, bool], data)

        active = _parse_active(d.pop("active", UNSET))

        def _parse_drift_window(
            data: object,
        ) -> Union["AssaysFilterBodyDriftWindowType0", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                drift_window_type_0 = AssaysFilterBodyDriftWindowType0.from_dict(data)

                return drift_window_type_0
            except:  # noqa: E722
                pass
            return cast(Union["AssaysFilterBodyDriftWindowType0", None, Unset], data)

        drift_window = _parse_drift_window(d.pop("drift_window", UNSET))

        def _parse_locations(data: object) -> Union[None, Unset, list[str]]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                locations_type_0 = cast(list[str], data)

                return locations_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, list[str]], data)

        locations = _parse_locations(d.pop("locations", UNSET))

        assays_filter_body = cls(
            workspace_id=workspace_id,
            pipeline_id=pipeline_id,
            sort_by=sort_by,
            name=name,
            active=active,
            drift_window=drift_window,
            locations=locations,
        )

        assays_filter_body.additional_properties = d
        return assays_filter_body

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
