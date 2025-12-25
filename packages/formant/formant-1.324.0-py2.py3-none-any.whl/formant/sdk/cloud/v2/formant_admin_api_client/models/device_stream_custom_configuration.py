from typing import Any, Dict, List, Type, TypeVar

import attr

from ..models.device_stream_custom_configuration_type import \
    DeviceStreamCustomConfigurationType

T = TypeVar("T", bound="DeviceStreamCustomConfiguration")

@attr.s(auto_attribs=True)
class DeviceStreamCustomConfiguration:
    """
    Attributes:
        type (DeviceStreamCustomConfigurationType):
    """

    type: DeviceStreamCustomConfigurationType
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        type = self.type.value


        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "type": type,
        })

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        type = DeviceStreamCustomConfigurationType(d.pop("type"))




        device_stream_custom_configuration = cls(
            type=type,
        )

        device_stream_custom_configuration.additional_properties = d
        return device_stream_custom_configuration

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
