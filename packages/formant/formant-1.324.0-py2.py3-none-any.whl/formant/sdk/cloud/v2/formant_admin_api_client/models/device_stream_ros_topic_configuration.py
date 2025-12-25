from typing import Any, Dict, List, Type, TypeVar, Union

import attr

from ..models.device_stream_ros_topic_configuration_ros_version import \
    DeviceStreamRosTopicConfigurationRosVersion
from ..models.device_stream_ros_topic_configuration_type import \
    DeviceStreamRosTopicConfigurationType
from ..types import UNSET, Unset

T = TypeVar("T", bound="DeviceStreamRosTopicConfiguration")

@attr.s(auto_attribs=True)
class DeviceStreamRosTopicConfiguration:
    """
    Attributes:
        type (DeviceStreamRosTopicConfigurationType):
        topic (str):
        ros_version (DeviceStreamRosTopicConfigurationRosVersion):
        path (Union[Unset, str]):
    """

    type: DeviceStreamRosTopicConfigurationType
    topic: str
    ros_version: DeviceStreamRosTopicConfigurationRosVersion
    path: Union[Unset, str] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        type = self.type.value

        topic = self.topic
        ros_version = self.ros_version.value

        path = self.path

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "type": type,
            "topic": topic,
            "rosVersion": ros_version,
        })
        if path is not UNSET:
            field_dict["path"] = path

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        type = DeviceStreamRosTopicConfigurationType(d.pop("type"))




        topic = d.pop("topic")

        ros_version = DeviceStreamRosTopicConfigurationRosVersion(d.pop("rosVersion"))




        path = d.pop("path", UNSET)

        device_stream_ros_topic_configuration = cls(
            type=type,
            topic=topic,
            ros_version=ros_version,
            path=path,
        )

        device_stream_ros_topic_configuration.additional_properties = d
        return device_stream_ros_topic_configuration

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
