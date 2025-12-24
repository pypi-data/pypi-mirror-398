import datetime
from collections.abc import Mapping
from typing import (
    Any,
    TypeVar,
    Union,
    cast,
)

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)
from dateutil.parser import isoparse

from ..types import UNSET, Unset

T = TypeVar(
    "T", bound="AssaysFilterResponse200ItemBaselineType0CalculatedType1FixedWindow"
)


@_attrs_define
class AssaysFilterResponse200ItemBaselineType0CalculatedType1FixedWindow:
    """Assay window.

    Attributes:
        path (str):  Window data path
        pipeline_name (str):  Pipeline name.
        width (str):  Window width.
        workspace_id (int):
        interval (Union[None, Unset, str]):  Window interval.
        model_name (Union[None, Unset, str]):  Model name.
        start (Union[None, Unset, datetime.datetime]):  Window start definition.
        locations (Union[None, Unset, list[str]]):  The list of locations the window can come from.
    """

    path: str
    pipeline_name: str
    width: str
    workspace_id: int
    interval: Union[None, Unset, str] = UNSET
    model_name: Union[None, Unset, str] = UNSET
    start: Union[None, Unset, datetime.datetime] = UNSET
    locations: Union[None, Unset, list[str]] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        path = self.path

        pipeline_name = self.pipeline_name

        width = self.width

        workspace_id = self.workspace_id

        interval: Union[None, Unset, str]
        if isinstance(self.interval, Unset):
            interval = UNSET
        else:
            interval = self.interval

        model_name: Union[None, Unset, str]
        if isinstance(self.model_name, Unset):
            model_name = UNSET
        else:
            model_name = self.model_name

        start: Union[None, Unset, str]
        if isinstance(self.start, Unset):
            start = UNSET
        elif isinstance(self.start, datetime.datetime):
            start = self.start.isoformat()
        else:
            start = self.start

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
                "path": path,
                "pipeline_name": pipeline_name,
                "width": width,
                "workspace_id": workspace_id,
            }
        )
        if interval is not UNSET:
            field_dict["interval"] = interval
        if model_name is not UNSET:
            field_dict["model_name"] = model_name
        if start is not UNSET:
            field_dict["start"] = start
        if locations is not UNSET:
            field_dict["locations"] = locations

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        path = d.pop("path")

        pipeline_name = d.pop("pipeline_name")

        width = d.pop("width")

        workspace_id = d.pop("workspace_id")

        def _parse_interval(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        interval = _parse_interval(d.pop("interval", UNSET))

        def _parse_model_name(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        model_name = _parse_model_name(d.pop("model_name", UNSET))

        def _parse_start(data: object) -> Union[None, Unset, datetime.datetime]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                start_type_0 = isoparse(data)

                return start_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, datetime.datetime], data)

        start = _parse_start(d.pop("start", UNSET))

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

        assays_filter_response_200_item_baseline_type_0_calculated_type_1_fixed_window = cls(
            path=path,
            pipeline_name=pipeline_name,
            width=width,
            workspace_id=workspace_id,
            interval=interval,
            model_name=model_name,
            start=start,
            locations=locations,
        )

        assays_filter_response_200_item_baseline_type_0_calculated_type_1_fixed_window.additional_properties = d
        return assays_filter_response_200_item_baseline_type_0_calculated_type_1_fixed_window

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
