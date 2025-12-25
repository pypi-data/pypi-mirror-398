from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

if TYPE_CHECKING:
  from ..models.user_teleop_twist_ros_topic_configuration import \
      UserTeleopTwistRosTopicConfiguration




T = TypeVar("T", bound="UserTeleopRosStreamConfiguration")

@attr.s(auto_attribs=True)
class UserTeleopRosStreamConfiguration:
    """
    Attributes:
        topic_name (str):
        display_name (Union[Unset, str]):
        configuration (Union[Unset, UserTeleopTwistRosTopicConfiguration]):
    """

    topic_name: str
    display_name: Union[Unset, str] = UNSET
    configuration: Union[Unset, 'UserTeleopTwistRosTopicConfiguration'] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        topic_name = self.topic_name
        display_name = self.display_name
        configuration: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.configuration, Unset):
            configuration = self.configuration.to_dict()


        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "topicName": topic_name,
        })
        if display_name is not UNSET:
            field_dict["displayName"] = display_name
        if configuration is not UNSET:
            field_dict["configuration"] = configuration

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.user_teleop_twist_ros_topic_configuration import \
            UserTeleopTwistRosTopicConfiguration
        d = src_dict.copy()
        topic_name = d.pop("topicName")

        display_name = d.pop("displayName", UNSET)

        _configuration = d.pop("configuration", UNSET)
        configuration: Union[Unset, UserTeleopTwistRosTopicConfiguration]
        if isinstance(_configuration,  Unset):
            configuration = UNSET
        else:
            configuration = UserTeleopTwistRosTopicConfiguration.from_dict(_configuration)




        user_teleop_ros_stream_configuration = cls(
            topic_name=topic_name,
            display_name=display_name,
            configuration=configuration,
        )

        user_teleop_ros_stream_configuration.additional_properties = d
        return user_teleop_ros_stream_configuration

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
