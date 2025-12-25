from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar

import attr

if TYPE_CHECKING:
  from ..models.transform import Transform




T = TypeVar("T", bound="Path")

@attr.s(auto_attribs=True)
class Path:
    """
    Attributes:
        world_to_local (Transform):
        poses (List['Transform']):
    """

    world_to_local: 'Transform'
    poses: List['Transform']
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        world_to_local = self.world_to_local.to_dict()

        poses = []
        for poses_item_data in self.poses:
            poses_item = poses_item_data.to_dict()

            poses.append(poses_item)





        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "worldToLocal": world_to_local,
            "poses": poses,
        })

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.transform import Transform
        d = src_dict.copy()
        world_to_local = Transform.from_dict(d.pop("worldToLocal"))




        poses = []
        _poses = d.pop("poses")
        for poses_item_data in (_poses):
            poses_item = Transform.from_dict(poses_item_data)



            poses.append(poses_item)


        path = cls(
            world_to_local=world_to_local,
            poses=poses,
        )

        path.additional_properties = d
        return path

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
