from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar

import attr

if TYPE_CHECKING:
  from ..models.location import Location




T = TypeVar("T", bound="LocationViewport")

@attr.s(auto_attribs=True)
class LocationViewport:
    """
    Attributes:
        center (Location):
        zoom (float):
    """

    center: 'Location'
    zoom: float
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        center = self.center.to_dict()

        zoom = self.zoom

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "center": center,
            "zoom": zoom,
        })

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.location import Location
        d = src_dict.copy()
        center = Location.from_dict(d.pop("center"))




        zoom = d.pop("zoom")

        location_viewport = cls(
            center=center,
            zoom=zoom,
        )

        location_viewport.additional_properties = d
        return location_viewport

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
