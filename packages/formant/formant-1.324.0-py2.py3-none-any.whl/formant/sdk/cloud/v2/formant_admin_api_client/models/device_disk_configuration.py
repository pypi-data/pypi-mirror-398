from typing import Any, Dict, List, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

T = TypeVar("T", bound="DeviceDiskConfiguration")

@attr.s(auto_attribs=True)
class DeviceDiskConfiguration:
    """
    Attributes:
        buffer_size (Union[Unset, int]):
        on_demand_buffer_size (Union[Unset, int]):
    """

    buffer_size: Union[Unset, int] = UNSET
    on_demand_buffer_size: Union[Unset, int] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        buffer_size = self.buffer_size
        on_demand_buffer_size = self.on_demand_buffer_size

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
        })
        if buffer_size is not UNSET:
            field_dict["bufferSize"] = buffer_size
        if on_demand_buffer_size is not UNSET:
            field_dict["onDemandBufferSize"] = on_demand_buffer_size

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        buffer_size = d.pop("bufferSize", UNSET)

        on_demand_buffer_size = d.pop("onDemandBufferSize", UNSET)

        device_disk_configuration = cls(
            buffer_size=buffer_size,
            on_demand_buffer_size=on_demand_buffer_size,
        )

        device_disk_configuration.additional_properties = d
        return device_disk_configuration

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
