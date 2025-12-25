from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

if TYPE_CHECKING:
  from ..models.transform import Transform




T = TypeVar("T", bound="PointCloud")

@attr.s(auto_attribs=True)
class PointCloud:
    """
    Attributes:
        url (str):
        size (Union[Unset, int]):
        world_to_local (Union[Unset, Transform]):
    """

    url: str
    size: Union[Unset, int] = UNSET
    world_to_local: Union[Unset, 'Transform'] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        url = self.url
        size = self.size
        world_to_local: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.world_to_local, Unset):
            world_to_local = self.world_to_local.to_dict()


        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "url": url,
        })
        if size is not UNSET:
            field_dict["size"] = size
        if world_to_local is not UNSET:
            field_dict["worldToLocal"] = world_to_local

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.transform import Transform
        d = src_dict.copy()
        url = d.pop("url")

        size = d.pop("size", UNSET)

        _world_to_local = d.pop("worldToLocal", UNSET)
        world_to_local: Union[Unset, Transform]
        if isinstance(_world_to_local,  Unset):
            world_to_local = UNSET
        else:
            world_to_local = Transform.from_dict(_world_to_local)




        point_cloud = cls(
            url=url,
            size=size,
            world_to_local=world_to_local,
        )

        point_cloud.additional_properties = d
        return point_cloud

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
