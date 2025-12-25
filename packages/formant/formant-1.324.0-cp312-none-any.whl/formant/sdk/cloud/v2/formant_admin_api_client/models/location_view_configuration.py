from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union

import attr

from ..models.location_view_configuration_basemap import \
    LocationViewConfigurationBasemap
from ..types import UNSET, Unset

if TYPE_CHECKING:
  from ..models.location_viewport import LocationViewport




T = TypeVar("T", bound="LocationViewConfiguration")

@attr.s(auto_attribs=True)
class LocationViewConfiguration:
    """
    Attributes:
        basemap (Union[Unset, LocationViewConfigurationBasemap]):
        viewport (Union[Unset, LocationViewport]):
    """

    basemap: Union[Unset, LocationViewConfigurationBasemap] = UNSET
    viewport: Union[Unset, 'LocationViewport'] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        basemap: Union[Unset, str] = UNSET
        if not isinstance(self.basemap, Unset):
            basemap = self.basemap.value

        viewport: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.viewport, Unset):
            viewport = self.viewport.to_dict()


        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
        })
        if basemap is not UNSET:
            field_dict["basemap"] = basemap
        if viewport is not UNSET:
            field_dict["viewport"] = viewport

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.location_viewport import LocationViewport
        d = src_dict.copy()
        _basemap = d.pop("basemap", UNSET)
        basemap: Union[Unset, LocationViewConfigurationBasemap]
        if isinstance(_basemap,  Unset):
            basemap = UNSET
        else:
            basemap = LocationViewConfigurationBasemap(_basemap)




        _viewport = d.pop("viewport", UNSET)
        viewport: Union[Unset, LocationViewport]
        if isinstance(_viewport,  Unset):
            viewport = UNSET
        else:
            viewport = LocationViewport.from_dict(_viewport)




        location_view_configuration = cls(
            basemap=basemap,
            viewport=viewport,
        )

        location_view_configuration.additional_properties = d
        return location_view_configuration

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
