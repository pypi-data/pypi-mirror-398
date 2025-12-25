from typing import Any, Dict, List, Type, TypeVar

import attr

from ..models.event_sort_column import EventSortColumn
from ..models.event_sort_order import EventSortOrder

T = TypeVar("T", bound="EventSort")

@attr.s(auto_attribs=True)
class EventSort:
    """
    Attributes:
        column (EventSortColumn):
        order (EventSortOrder):
    """

    column: EventSortColumn
    order: EventSortOrder
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
        column = EventSortColumn(d.pop("column"))




        order = EventSortOrder(d.pop("order"))




        event_sort = cls(
            column=column,
            order=order,
        )

        event_sort.additional_properties = d
        return event_sort

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
