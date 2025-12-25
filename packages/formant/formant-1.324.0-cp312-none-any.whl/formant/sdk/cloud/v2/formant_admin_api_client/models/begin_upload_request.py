from typing import Any, Dict, List, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

T = TypeVar("T", bound="BeginUploadRequest")

@attr.s(auto_attribs=True)
class BeginUploadRequest:
    """
    Attributes:
        file_name (str):
        file_size (int):
        force_overwrite (Union[Unset, bool]):
        content_type (Union[Unset, str]):
    """

    file_name: str
    file_size: int
    force_overwrite: Union[Unset, bool] = UNSET
    content_type: Union[Unset, str] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        file_name = self.file_name
        file_size = self.file_size
        force_overwrite = self.force_overwrite
        content_type = self.content_type

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "fileName": file_name,
            "fileSize": file_size,
        })
        if force_overwrite is not UNSET:
            field_dict["forceOverwrite"] = force_overwrite
        if content_type is not UNSET:
            field_dict["contentType"] = content_type

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        file_name = d.pop("fileName")

        file_size = d.pop("fileSize")

        force_overwrite = d.pop("forceOverwrite", UNSET)

        content_type = d.pop("contentType", UNSET)

        begin_upload_request = cls(
            file_name=file_name,
            file_size=file_size,
            force_overwrite=force_overwrite,
            content_type=content_type,
        )

        begin_upload_request.additional_properties = d
        return begin_upload_request

    @property
    def additional_keys(self) -> List[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
