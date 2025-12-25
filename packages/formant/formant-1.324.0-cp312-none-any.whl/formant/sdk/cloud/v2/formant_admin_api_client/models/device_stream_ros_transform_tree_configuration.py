from typing import Any, Dict, List, Type, TypeVar

import attr

from ..models.device_stream_ros_transform_tree_configuration_ros_version import \
    DeviceStreamRosTransformTreeConfigurationRosVersion
from ..models.device_stream_ros_transform_tree_configuration_type import \
    DeviceStreamRosTransformTreeConfigurationType

T = TypeVar("T", bound="DeviceStreamRosTransformTreeConfiguration")

@attr.s(auto_attribs=True)
class DeviceStreamRosTransformTreeConfiguration:
    """
    Attributes:
        type (DeviceStreamRosTransformTreeConfigurationType):
        base_reference_frame (str):
        ros_version (DeviceStreamRosTransformTreeConfigurationRosVersion):
    """

    type: DeviceStreamRosTransformTreeConfigurationType
    base_reference_frame: str
    ros_version: DeviceStreamRosTransformTreeConfigurationRosVersion
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        type = self.type.value

        base_reference_frame = self.base_reference_frame
        ros_version = self.ros_version.value


        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "type": type,
            "baseReferenceFrame": base_reference_frame,
            "rosVersion": ros_version,
        })

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        type = DeviceStreamRosTransformTreeConfigurationType(d.pop("type"))




        base_reference_frame = d.pop("baseReferenceFrame")

        ros_version = DeviceStreamRosTransformTreeConfigurationRosVersion(d.pop("rosVersion"))




        device_stream_ros_transform_tree_configuration = cls(
            type=type,
            base_reference_frame=base_reference_frame,
            ros_version=ros_version,
        )

        device_stream_ros_transform_tree_configuration.additional_properties = d
        return device_stream_ros_transform_tree_configuration

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
