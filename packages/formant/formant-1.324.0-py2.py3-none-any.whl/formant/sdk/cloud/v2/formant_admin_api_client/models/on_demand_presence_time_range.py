from typing import Any, Dict, List, Type, TypeVar

import attr

T = TypeVar("T", bound="OnDemandPresenceTimeRange")

@attr.s(auto_attribs=True)
class OnDemandPresenceTimeRange:
    """
    Attributes:
        start (int):
        end (int):
        byte_size (float):
        item_count (float):
    """

    start: int
    end: int
    byte_size: float
    item_count: float
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        start = self.start
        end = self.end
        byte_size = self.byte_size
        item_count = self.item_count

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "start": start,
            "end": end,
            "byteSize": byte_size,
            "itemCount": item_count,
        })

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        start = d.pop("start")

        end = d.pop("end")

        byte_size = d.pop("byteSize")

        item_count = d.pop("itemCount")

        on_demand_presence_time_range = cls(
            start=start,
            end=end,
            byte_size=byte_size,
            item_count=item_count,
        )

        on_demand_presence_time_range.additional_properties = d
        return on_demand_presence_time_range

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
