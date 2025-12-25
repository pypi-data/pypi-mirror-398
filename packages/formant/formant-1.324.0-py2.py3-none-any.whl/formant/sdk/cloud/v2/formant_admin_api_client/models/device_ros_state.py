from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar

import attr

if TYPE_CHECKING:
  from ..models.ros_topic import RosTopic




T = TypeVar("T", bound="DeviceRosState")

@attr.s(auto_attribs=True)
class DeviceRosState:
    """
    Attributes:
        topics (List['RosTopic']):
    """

    topics: List['RosTopic']
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        topics = []
        for topics_item_data in self.topics:
            topics_item = topics_item_data.to_dict()

            topics.append(topics_item)





        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "topics": topics,
        })

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.ros_topic import RosTopic
        d = src_dict.copy()
        topics = []
        _topics = d.pop("topics")
        for topics_item_data in (_topics):
            topics_item = RosTopic.from_dict(topics_item_data)



            topics.append(topics_item)


        device_ros_state = cls(
            topics=topics,
        )

        device_ros_state.additional_properties = d
        return device_ros_state

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
