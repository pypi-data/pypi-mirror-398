from typing import Any, Dict, List, Type, TypeVar

import attr

from ..models.device_details_sort_column import DeviceDetailsSortColumn
from ..models.device_details_sort_order import DeviceDetailsSortOrder

T = TypeVar("T", bound="DeviceDetailsSort")

@attr.s(auto_attribs=True)
class DeviceDetailsSort:
    """
    Attributes:
        column (DeviceDetailsSortColumn):
        order (DeviceDetailsSortOrder):
    """

    column: DeviceDetailsSortColumn
    order: DeviceDetailsSortOrder
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        column = self.column.value

        order = self.order.value


        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "column": column,
            "order": order,
        })

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        column = DeviceDetailsSortColumn(d.pop("column"))




        order = DeviceDetailsSortOrder(d.pop("order"))




        device_details_sort = cls(
            column=column,
            order=order,
        )

        device_details_sort.additional_properties = d
        return device_details_sort

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
