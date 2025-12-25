from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

if TYPE_CHECKING:
  from ..models.device_configuration import DeviceConfiguration




T = TypeVar("T", bound="UpdatedConfigurationResponse")

@attr.s(auto_attribs=True)
class UpdatedConfigurationResponse:
    """
    Attributes:
        desired_configuration (Union[Unset, None, DeviceConfiguration]):
    """

    desired_configuration: Union[Unset, None, 'DeviceConfiguration'] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        desired_configuration: Union[Unset, None, Dict[str, Any]] = UNSET
        if not isinstance(self.desired_configuration, Unset):
            desired_configuration = self.desired_configuration.to_dict() if self.desired_configuration else None


        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
        })
        if desired_configuration is not UNSET:
            field_dict["desiredConfiguration"] = desired_configuration

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.device_configuration import DeviceConfiguration
        d = src_dict.copy()
        _desired_configuration = d.pop("desiredConfiguration", UNSET)
        desired_configuration: Union[Unset, None, DeviceConfiguration]
        if _desired_configuration is None:
            desired_configuration = None
        elif isinstance(_desired_configuration,  Unset):
            desired_configuration = UNSET
        else:
            desired_configuration = DeviceConfiguration.from_dict(_desired_configuration)




        updated_configuration_response = cls(
            desired_configuration=desired_configuration,
        )

        updated_configuration_response.additional_properties = d
        return updated_configuration_response

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
