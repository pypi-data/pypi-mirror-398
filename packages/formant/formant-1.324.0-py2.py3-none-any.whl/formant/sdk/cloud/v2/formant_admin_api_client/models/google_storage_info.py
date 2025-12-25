from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union

import attr

from ..models.google_storage_info_output_format import \
    GoogleStorageInfoOutputFormat
from ..types import UNSET, Unset

if TYPE_CHECKING:
  from ..models.google_storage_export import GoogleStorageExport




T = TypeVar("T", bound="GoogleStorageInfo")

@attr.s(auto_attribs=True)
class GoogleStorageInfo:
    """
    Attributes:
        credentials_json_key (str):
        google_storage_export (Union[Unset, GoogleStorageExport]):
        output_format (Union[Unset, GoogleStorageInfoOutputFormat]):
    """

    credentials_json_key: str
    google_storage_export: Union[Unset, 'GoogleStorageExport'] = UNSET
    output_format: Union[Unset, GoogleStorageInfoOutputFormat] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        credentials_json_key = self.credentials_json_key
        google_storage_export: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.google_storage_export, Unset):
            google_storage_export = self.google_storage_export.to_dict()

        output_format: Union[Unset, str] = UNSET
        if not isinstance(self.output_format, Unset):
            output_format = self.output_format.value


        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "credentialsJsonKey": credentials_json_key,
        })
        if google_storage_export is not UNSET:
            field_dict["googleStorageExport"] = google_storage_export
        if output_format is not UNSET:
            field_dict["outputFormat"] = output_format

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.google_storage_export import GoogleStorageExport
        d = src_dict.copy()
        credentials_json_key = d.pop("credentialsJsonKey")

        _google_storage_export = d.pop("googleStorageExport", UNSET)
        google_storage_export: Union[Unset, GoogleStorageExport]
        if isinstance(_google_storage_export,  Unset):
            google_storage_export = UNSET
        else:
            google_storage_export = GoogleStorageExport.from_dict(_google_storage_export)




        _output_format = d.pop("outputFormat", UNSET)
        output_format: Union[Unset, GoogleStorageInfoOutputFormat]
        if isinstance(_output_format,  Unset):
            output_format = UNSET
        else:
            output_format = GoogleStorageInfoOutputFormat(_output_format)




        google_storage_info = cls(
            credentials_json_key=credentials_json_key,
            google_storage_export=google_storage_export,
            output_format=output_format,
        )

        google_storage_info.additional_properties = d
        return google_storage_info

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
