import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar

import attr
from dateutil.parser import isoparse

if TYPE_CHECKING:
  from ..models.event_counts import EventCounts




T = TypeVar("T", bound="EventHistogramEntry")

@attr.s(auto_attribs=True)
class EventHistogramEntry:
    """
    Attributes:
        time (datetime.datetime):
        counts (EventCounts):
    """

    time: datetime.datetime
    counts: 'EventCounts'
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        time = self.time.isoformat()

        counts = self.counts.to_dict()


        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "time": time,
            "counts": counts,
        })

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.event_counts import EventCounts
        d = src_dict.copy()
        time = isoparse(d.pop("time"))




        counts = EventCounts.from_dict(d.pop("counts"))




        event_histogram_entry = cls(
            time=time,
            counts=counts,
        )

        event_histogram_entry.additional_properties = d
        return event_histogram_entry

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
