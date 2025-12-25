from typing import Any, Dict, List, Type, TypeVar

import attr

T = TypeVar("T", bound="DeviceStreamConfigurationTags")

@attr.s(auto_attribs=True)
class DeviceStreamConfigurationTags:
    """
    """

    additional_properties: Dict[str, str] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        
        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
        })

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        device_stream_configuration_tags = cls(
        )


        device_stream_configuration_tags.additional_properties = d
        return device_stream_configuration_tags

    @property
    def additional_keys(self) -> List[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> str:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: str) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
