from typing import Any, Dict, List, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

T = TypeVar("T", bound="Location")

@attr.s(auto_attribs=True)
class Location:
    """
    Attributes:
        latitude (float):
        longitude (float):
        altitude (Union[Unset, float]):
        orientation (Union[Unset, float]):
    """

    latitude: float
    longitude: float
    altitude: Union[Unset, float] = UNSET
    orientation: Union[Unset, float] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        latitude = self.latitude
        longitude = self.longitude
        altitude = self.altitude
        orientation = self.orientation

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "latitude": latitude,
            "longitude": longitude,
        })
        if altitude is not UNSET:
            field_dict["altitude"] = altitude
        if orientation is not UNSET:
            field_dict["orientation"] = orientation

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        latitude = d.pop("latitude")

        longitude = d.pop("longitude")

        altitude = d.pop("altitude", UNSET)

        orientation = d.pop("orientation", UNSET)

        location = cls(
            latitude=latitude,
            longitude=longitude,
            altitude=altitude,
            orientation=orientation,
        )

        location.additional_properties = d
        return location

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
