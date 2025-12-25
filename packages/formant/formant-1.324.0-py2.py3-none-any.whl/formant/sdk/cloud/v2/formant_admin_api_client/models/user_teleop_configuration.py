from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

if TYPE_CHECKING:
  from ..models.user_teleop_ros_stream_configuration import \
      UserTeleopRosStreamConfiguration




T = TypeVar("T", bound="UserTeleopConfiguration")

@attr.s(auto_attribs=True)
class UserTeleopConfiguration:
    """
    Attributes:
        ros_streams (Union[Unset, List['UserTeleopRosStreamConfiguration']]):
    """

    ros_streams: Union[Unset, List['UserTeleopRosStreamConfiguration']] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        ros_streams: Union[Unset, List[Dict[str, Any]]] = UNSET
        if not isinstance(self.ros_streams, Unset):
            ros_streams = []
            for ros_streams_item_data in self.ros_streams:
                ros_streams_item = ros_streams_item_data.to_dict()

                ros_streams.append(ros_streams_item)





        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
        })
        if ros_streams is not UNSET:
            field_dict["rosStreams"] = ros_streams

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.user_teleop_ros_stream_configuration import \
            UserTeleopRosStreamConfiguration
        d = src_dict.copy()
        ros_streams = []
        _ros_streams = d.pop("rosStreams", UNSET)
        for ros_streams_item_data in (_ros_streams or []):
            ros_streams_item = UserTeleopRosStreamConfiguration.from_dict(ros_streams_item_data)



            ros_streams.append(ros_streams_item)


        user_teleop_configuration = cls(
            ros_streams=ros_streams,
        )

        user_teleop_configuration.additional_properties = d
        return user_teleop_configuration

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
