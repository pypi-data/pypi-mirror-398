from typing import Any, Dict, List, Type, TypeVar, Union

import attr

from ..models.device_stream_directory_watch_configuration_file_type import \
    DeviceStreamDirectoryWatchConfigurationFileType
from ..models.device_stream_directory_watch_configuration_type import \
    DeviceStreamDirectoryWatchConfigurationType
from ..types import UNSET, Unset

T = TypeVar("T", bound="DeviceStreamDirectoryWatchConfiguration")

@attr.s(auto_attribs=True)
class DeviceStreamDirectoryWatchConfiguration:
    """
    Attributes:
        type (DeviceStreamDirectoryWatchConfigurationType):
        directory (str):
        extension (Union[Unset, str]):
        file_type (Union[Unset, DeviceStreamDirectoryWatchConfigurationFileType]):
    """

    type: DeviceStreamDirectoryWatchConfigurationType
    directory: str
    extension: Union[Unset, str] = UNSET
    file_type: Union[Unset, DeviceStreamDirectoryWatchConfigurationFileType] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        type = self.type.value

        directory = self.directory
        extension = self.extension
        file_type: Union[Unset, str] = UNSET
        if not isinstance(self.file_type, Unset):
            file_type = self.file_type.value


        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "type": type,
            "directory": directory,
        })
        if extension is not UNSET:
            field_dict["extension"] = extension
        if file_type is not UNSET:
            field_dict["fileType"] = file_type

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        type = DeviceStreamDirectoryWatchConfigurationType(d.pop("type"))




        directory = d.pop("directory")

        extension = d.pop("extension", UNSET)

        _file_type = d.pop("fileType", UNSET)
        file_type: Union[Unset, DeviceStreamDirectoryWatchConfigurationFileType]
        if isinstance(_file_type,  Unset):
            file_type = UNSET
        else:
            file_type = DeviceStreamDirectoryWatchConfigurationFileType(_file_type)




        device_stream_directory_watch_configuration = cls(
            type=type,
            directory=directory,
            extension=extension,
            file_type=file_type,
        )

        device_stream_directory_watch_configuration.additional_properties = d
        return device_stream_directory_watch_configuration

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
