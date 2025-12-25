from typing import Any, Dict, List, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

T = TypeVar("T", bound="Battery")

@attr.s(auto_attribs=True)
class Battery:
    """
    Attributes:
        percentage (float):
        voltage (Union[Unset, float]):
        current (Union[Unset, float]):
        charge (Union[Unset, float]):
    """

    percentage: float
    voltage: Union[Unset, float] = UNSET
    current: Union[Unset, float] = UNSET
    charge: Union[Unset, float] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        percentage = self.percentage
        voltage = self.voltage
        current = self.current
        charge = self.charge

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "percentage": percentage,
        })
        if voltage is not UNSET:
            field_dict["voltage"] = voltage
        if current is not UNSET:
            field_dict["current"] = current
        if charge is not UNSET:
            field_dict["charge"] = charge

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        percentage = d.pop("percentage")

        voltage = d.pop("voltage", UNSET)

        current = d.pop("current", UNSET)

        charge = d.pop("charge", UNSET)

        battery = cls(
            percentage=percentage,
            voltage=voltage,
            current=current,
            charge=charge,
        )

        battery.additional_properties = d
        return battery

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
