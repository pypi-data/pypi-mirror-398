from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar

import attr

from ..models.user_teleop_twist_ros_topic_configuration_type import \
    UserTeleopTwistRosTopicConfigurationType

if TYPE_CHECKING:
  from ..models.joystick_configuration import JoystickConfiguration




T = TypeVar("T", bound="UserTeleopTwistRosTopicConfiguration")

@attr.s(auto_attribs=True)
class UserTeleopTwistRosTopicConfiguration:
    """
    Attributes:
        type (UserTeleopTwistRosTopicConfigurationType):
        joystick (JoystickConfiguration):
    """

    type: UserTeleopTwistRosTopicConfigurationType
    joystick: 'JoystickConfiguration'
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        type = self.type.value

        joystick = self.joystick.to_dict()


        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "type": type,
            "joystick": joystick,
        })

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.joystick_configuration import JoystickConfiguration
        d = src_dict.copy()
        type = UserTeleopTwistRosTopicConfigurationType(d.pop("type"))




        joystick = JoystickConfiguration.from_dict(d.pop("joystick"))




        user_teleop_twist_ros_topic_configuration = cls(
            type=type,
            joystick=joystick,
        )

        user_teleop_twist_ros_topic_configuration.additional_properties = d
        return user_teleop_twist_ros_topic_configuration

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
