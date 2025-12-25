from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar

import attr

if TYPE_CHECKING:
  from ..models.event_counts import EventCounts




T = TypeVar("T", bound="EventCountsByDevice")

@attr.s(auto_attribs=True)
class EventCountsByDevice:
    """
    Attributes:
        counts (List['EventCounts']):
    """

    counts: List['EventCounts']
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        counts = []
        for counts_item_data in self.counts:
            counts_item = counts_item_data.to_dict()

            counts.append(counts_item)





        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "counts": counts,
        })

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.event_counts import EventCounts
        d = src_dict.copy()
        counts = []
        _counts = d.pop("counts")
        for counts_item_data in (_counts):
            counts_item = EventCounts.from_dict(counts_item_data)



            counts.append(counts_item)


        event_counts_by_device = cls(
            counts=counts,
        )

        event_counts_by_device.additional_properties = d
        return event_counts_by_device

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
