from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar

import attr

if TYPE_CHECKING:
  from ..models.transform import Transform
  from ..models.twist import Twist




T = TypeVar("T", bound="Odometry")

@attr.s(auto_attribs=True)
class Odometry:
    """
    Attributes:
        pose (Transform):
        twist (Twist):
        world_to_local (Transform):
    """

    pose: 'Transform'
    twist: 'Twist'
    world_to_local: 'Transform'
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        pose = self.pose.to_dict()

        twist = self.twist.to_dict()

        world_to_local = self.world_to_local.to_dict()


        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "pose": pose,
            "twist": twist,
            "worldToLocal": world_to_local,
        })

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.transform import Transform
        from ..models.twist import Twist
        d = src_dict.copy()
        pose = Transform.from_dict(d.pop("pose"))




        twist = Twist.from_dict(d.pop("twist"))




        world_to_local = Transform.from_dict(d.pop("worldToLocal"))




        odometry = cls(
            pose=pose,
            twist=twist,
            world_to_local=world_to_local,
        )

        odometry.additional_properties = d
        return odometry

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
