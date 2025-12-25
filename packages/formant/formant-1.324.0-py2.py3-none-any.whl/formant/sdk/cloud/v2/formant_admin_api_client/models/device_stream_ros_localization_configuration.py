from typing import Any, Dict, List, Type, TypeVar, Union, cast

import attr

from ..models.device_stream_ros_localization_configuration_ros_version import \
    DeviceStreamRosLocalizationConfigurationRosVersion
from ..models.device_stream_ros_localization_configuration_type import \
    DeviceStreamRosLocalizationConfigurationType
from ..types import UNSET, Unset

T = TypeVar("T", bound="DeviceStreamRosLocalizationConfiguration")

@attr.s(auto_attribs=True)
class DeviceStreamRosLocalizationConfiguration:
    """
    Attributes:
        type (DeviceStreamRosLocalizationConfigurationType):
        base_reference_frame (str):
        odom_topic (str):
        ros_version (DeviceStreamRosLocalizationConfigurationRosVersion):
        map_topic (Union[Unset, str]):
        point_cloud_topics (Union[Unset, List[str]]):
        path_topic (Union[Unset, str]):
        goal_topic (Union[Unset, str]):
    """

    type: DeviceStreamRosLocalizationConfigurationType
    base_reference_frame: str
    odom_topic: str
    ros_version: DeviceStreamRosLocalizationConfigurationRosVersion
    map_topic: Union[Unset, str] = UNSET
    point_cloud_topics: Union[Unset, List[str]] = UNSET
    path_topic: Union[Unset, str] = UNSET
    goal_topic: Union[Unset, str] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        type = self.type.value

        base_reference_frame = self.base_reference_frame
        odom_topic = self.odom_topic
        ros_version = self.ros_version.value

        map_topic = self.map_topic
        point_cloud_topics: Union[Unset, List[str]] = UNSET
        if not isinstance(self.point_cloud_topics, Unset):
            point_cloud_topics = self.point_cloud_topics




        path_topic = self.path_topic
        goal_topic = self.goal_topic

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "type": type,
            "baseReferenceFrame": base_reference_frame,
            "odomTopic": odom_topic,
            "rosVersion": ros_version,
        })
        if map_topic is not UNSET:
            field_dict["mapTopic"] = map_topic
        if point_cloud_topics is not UNSET:
            field_dict["pointCloudTopics"] = point_cloud_topics
        if path_topic is not UNSET:
            field_dict["pathTopic"] = path_topic
        if goal_topic is not UNSET:
            field_dict["goalTopic"] = goal_topic

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        type = DeviceStreamRosLocalizationConfigurationType(d.pop("type"))




        base_reference_frame = d.pop("baseReferenceFrame")

        odom_topic = d.pop("odomTopic")

        ros_version = DeviceStreamRosLocalizationConfigurationRosVersion(d.pop("rosVersion"))




        map_topic = d.pop("mapTopic", UNSET)

        point_cloud_topics = cast(List[str], d.pop("pointCloudTopics", UNSET))


        path_topic = d.pop("pathTopic", UNSET)

        goal_topic = d.pop("goalTopic", UNSET)

        device_stream_ros_localization_configuration = cls(
            type=type,
            base_reference_frame=base_reference_frame,
            odom_topic=odom_topic,
            ros_version=ros_version,
            map_topic=map_topic,
            point_cloud_topics=point_cloud_topics,
            path_topic=path_topic,
            goal_topic=goal_topic,
        )

        device_stream_ros_localization_configuration.additional_properties = d
        return device_stream_ros_localization_configuration

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
