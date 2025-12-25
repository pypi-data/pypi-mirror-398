from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar

import attr

if TYPE_CHECKING:
  from ..models.geo_json_icon import GeoJsonIcon
  from ..models.geo_json_layer import GeoJsonLayer




T = TypeVar("T", bound="LocationModuleParameters")

@attr.s(auto_attribs=True)
class LocationModuleParameters:
    """
    Attributes:
        geo_json_layers (List['GeoJsonLayer']):
        geo_json_icons (List['GeoJsonIcon']):
    """

    geo_json_layers: List['GeoJsonLayer']
    geo_json_icons: List['GeoJsonIcon']
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        geo_json_layers = []
        for geo_json_layers_item_data in self.geo_json_layers:
            geo_json_layers_item = geo_json_layers_item_data.to_dict()

            geo_json_layers.append(geo_json_layers_item)




        geo_json_icons = []
        for geo_json_icons_item_data in self.geo_json_icons:
            geo_json_icons_item = geo_json_icons_item_data.to_dict()

            geo_json_icons.append(geo_json_icons_item)





        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "geoJsonLayers": geo_json_layers,
            "geoJsonIcons": geo_json_icons,
        })

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.geo_json_icon import GeoJsonIcon
        from ..models.geo_json_layer import GeoJsonLayer
        d = src_dict.copy()
        geo_json_layers = []
        _geo_json_layers = d.pop("geoJsonLayers")
        for geo_json_layers_item_data in (_geo_json_layers):
            geo_json_layers_item = GeoJsonLayer.from_dict(geo_json_layers_item_data)



            geo_json_layers.append(geo_json_layers_item)


        geo_json_icons = []
        _geo_json_icons = d.pop("geoJsonIcons")
        for geo_json_icons_item_data in (_geo_json_icons):
            geo_json_icons_item = GeoJsonIcon.from_dict(geo_json_icons_item_data)



            geo_json_icons.append(geo_json_icons_item)


        location_module_parameters = cls(
            geo_json_layers=geo_json_layers,
            geo_json_icons=geo_json_icons,
        )

        location_module_parameters.additional_properties = d
        return location_module_parameters

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
