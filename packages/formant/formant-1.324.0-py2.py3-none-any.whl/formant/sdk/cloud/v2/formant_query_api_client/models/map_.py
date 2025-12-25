from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

if TYPE_CHECKING:
  from ..models.transform import Transform




T = TypeVar("T", bound="Map")

@attr.s(auto_attribs=True)
class Map:
    """
    Attributes:
        url (str):
        width (int):
        height (int):
        resolution (float):
        origin (Transform):
        world_to_local (Transform):
        size (Union[Unset, int]):
    """

    url: str
    width: int
    height: int
    resolution: float
    origin: 'Transform'
    world_to_local: 'Transform'
    size: Union[Unset, int] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        url = self.url
        width = self.width
        height = self.height
        resolution = self.resolution
        origin = self.origin.to_dict()

        world_to_local = self.world_to_local.to_dict()

        size = self.size

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "url": url,
            "width": width,
            "height": height,
            "resolution": resolution,
            "origin": origin,
            "worldToLocal": world_to_local,
        })
        if size is not UNSET:
            field_dict["size"] = size

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.transform import Transform
        d = src_dict.copy()
        url = d.pop("url")

        width = d.pop("width")

        height = d.pop("height")

        resolution = d.pop("resolution")

        origin = Transform.from_dict(d.pop("origin"))




        world_to_local = Transform.from_dict(d.pop("worldToLocal"))




        size = d.pop("size", UNSET)

        map_ = cls(
            url=url,
            width=width,
            height=height,
            resolution=resolution,
            origin=origin,
            world_to_local=world_to_local,
            size=size,
        )

        map_.additional_properties = d
        return map_

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
