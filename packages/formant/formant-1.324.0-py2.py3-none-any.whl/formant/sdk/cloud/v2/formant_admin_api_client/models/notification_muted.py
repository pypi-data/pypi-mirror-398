import datetime
from typing import Any, Dict, List, Type, TypeVar

import attr
from dateutil.parser import isoparse

T = TypeVar("T", bound="NotificationMuted")

@attr.s(auto_attribs=True)
class NotificationMuted:
    """
    Attributes:
        start (datetime.datetime): Mute start time (inclusive).
        end (datetime.datetime): Mute end time (exclusive).
    """

    start: datetime.datetime
    end: datetime.datetime
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        start = self.start.isoformat()

        end = self.end.isoformat()


        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "start": start,
            "end": end,
        })

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        start = isoparse(d.pop("start"))




        end = isoparse(d.pop("end"))




        notification_muted = cls(
            start=start,
            end=end,
        )

        notification_muted.additional_properties = d
        return notification_muted

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
