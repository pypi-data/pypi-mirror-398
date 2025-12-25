from typing import Any, Dict, List, Type, TypeVar, Union

import attr

from ..models.device_stream_file_tail_configuration_file_format import \
    DeviceStreamFileTailConfigurationFileFormat
from ..models.device_stream_file_tail_configuration_type import \
    DeviceStreamFileTailConfigurationType
from ..types import UNSET, Unset

T = TypeVar("T", bound="DeviceStreamFileTailConfiguration")

@attr.s(auto_attribs=True)
class DeviceStreamFileTailConfiguration:
    """
    Attributes:
        type (DeviceStreamFileTailConfigurationType):
        filename (str):
        file_format (Union[Unset, DeviceStreamFileTailConfigurationFileFormat]):
        time_key (Union[Unset, str]):
        time_format (Union[Unset, str]):
        regex (Union[Unset, str]):
    """

    type: DeviceStreamFileTailConfigurationType
    filename: str
    file_format: Union[Unset, DeviceStreamFileTailConfigurationFileFormat] = UNSET
    time_key: Union[Unset, str] = UNSET
    time_format: Union[Unset, str] = UNSET
    regex: Union[Unset, str] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        type = self.type.value

        filename = self.filename
        file_format: Union[Unset, str] = UNSET
        if not isinstance(self.file_format, Unset):
            file_format = self.file_format.value

        time_key = self.time_key
        time_format = self.time_format
        regex = self.regex

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "type": type,
            "filename": filename,
        })
        if file_format is not UNSET:
            field_dict["fileFormat"] = file_format
        if time_key is not UNSET:
            field_dict["timeKey"] = time_key
        if time_format is not UNSET:
            field_dict["timeFormat"] = time_format
        if regex is not UNSET:
            field_dict["regex"] = regex

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        type = DeviceStreamFileTailConfigurationType(d.pop("type"))




        filename = d.pop("filename")

        _file_format = d.pop("fileFormat", UNSET)
        file_format: Union[Unset, DeviceStreamFileTailConfigurationFileFormat]
        if isinstance(_file_format,  Unset):
            file_format = UNSET
        else:
            file_format = DeviceStreamFileTailConfigurationFileFormat(_file_format)




        time_key = d.pop("timeKey", UNSET)

        time_format = d.pop("timeFormat", UNSET)

        regex = d.pop("regex", UNSET)

        device_stream_file_tail_configuration = cls(
            type=type,
            filename=filename,
            file_format=file_format,
            time_key=time_key,
            time_format=time_format,
            regex=regex,
        )

        device_stream_file_tail_configuration.additional_properties = d
        return device_stream_file_tail_configuration

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
