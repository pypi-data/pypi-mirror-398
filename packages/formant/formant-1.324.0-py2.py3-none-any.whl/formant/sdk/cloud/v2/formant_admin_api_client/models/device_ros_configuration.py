from typing import Any, Dict, List, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

T = TypeVar("T", bound="DeviceRosConfiguration")

@attr.s(auto_attribs=True)
class DeviceRosConfiguration:
    """
    Attributes:
        world_reference_frame_id (Union[Unset, str]):
    """

    world_reference_frame_id: Union[Unset, str] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        world_reference_frame_id = self.world_reference_frame_id

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
        })
        if world_reference_frame_id is not UNSET:
            field_dict["worldReferenceFrameId"] = world_reference_frame_id

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        world_reference_frame_id = d.pop("worldReferenceFrameId", UNSET)

        device_ros_configuration = cls(
            world_reference_frame_id=world_reference_frame_id,
        )

        device_ros_configuration.additional_properties = d
        return device_ros_configuration

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
