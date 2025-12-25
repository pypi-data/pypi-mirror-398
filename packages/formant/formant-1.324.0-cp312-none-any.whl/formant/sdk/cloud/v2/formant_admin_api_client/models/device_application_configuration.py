from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

if TYPE_CHECKING:
  from ..models.device_application_configuration_configuration_map import \
      DeviceApplicationConfigurationConfigurationMap




T = TypeVar("T", bound="DeviceApplicationConfiguration")

@attr.s(auto_attribs=True)
class DeviceApplicationConfiguration:
    """
    Attributes:
        configuration_map (Union[Unset, DeviceApplicationConfigurationConfigurationMap]):
    """

    configuration_map: Union[Unset, 'DeviceApplicationConfigurationConfigurationMap'] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        configuration_map: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.configuration_map, Unset):
            configuration_map = self.configuration_map.to_dict()


        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
        })
        if configuration_map is not UNSET:
            field_dict["configurationMap"] = configuration_map

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.device_application_configuration_configuration_map import \
            DeviceApplicationConfigurationConfigurationMap
        d = src_dict.copy()
        _configuration_map = d.pop("configurationMap", UNSET)
        configuration_map: Union[Unset, DeviceApplicationConfigurationConfigurationMap]
        if isinstance(_configuration_map,  Unset):
            configuration_map = UNSET
        else:
            configuration_map = DeviceApplicationConfigurationConfigurationMap.from_dict(_configuration_map)




        device_application_configuration = cls(
            configuration_map=configuration_map,
        )

        device_application_configuration.additional_properties = d
        return device_application_configuration

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
