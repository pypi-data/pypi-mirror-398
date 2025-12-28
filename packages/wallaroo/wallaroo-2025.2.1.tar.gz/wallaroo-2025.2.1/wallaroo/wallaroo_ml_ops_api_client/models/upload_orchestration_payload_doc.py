from collections.abc import Mapping
from io import BytesIO
from typing import (
    TYPE_CHECKING,
    Any,
    TypeVar,
)

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..types import File

if TYPE_CHECKING:
    from ..models.upload_orchestration_request import UploadOrchestrationRequest


T = TypeVar("T", bound="UploadOrchestrationPayloadDoc")


@_attrs_define
class UploadOrchestrationPayloadDoc:
    """
    Attributes:
        file (File):
        metadata (UploadOrchestrationRequest):
    """

    file: File
    metadata: "UploadOrchestrationRequest"
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        file = self.file.to_tuple()

        metadata = self.metadata.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "file": file,
                "metadata": metadata,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.upload_orchestration_request import UploadOrchestrationRequest

        d = dict(src_dict)
        file = File(payload=BytesIO(d.pop("file")))

        metadata = UploadOrchestrationRequest.from_dict(d.pop("metadata"))

        upload_orchestration_payload_doc = cls(
            file=file,
            metadata=metadata,
        )

        upload_orchestration_payload_doc.additional_properties = d
        return upload_orchestration_payload_doc

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
