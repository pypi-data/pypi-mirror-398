import datetime
from typing import Any, Dict, List, Type, TypeVar

import attr
from dateutil.parser import isoparse

T = TypeVar("T", bound="FocusedDatapoint")

@attr.s(auto_attribs=True)
class FocusedDatapoint:
    """
    Attributes:
        stream_name (str):
        time (datetime.datetime):
    """

    stream_name: str
    time: datetime.datetime
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        stream_name = self.stream_name
        time = self.time.isoformat()


        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "streamName": stream_name,
            "time": time,
        })

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        stream_name = d.pop("streamName")

        time = isoparse(d.pop("time"))




        focused_datapoint = cls(
            stream_name=stream_name,
            time=time,
        )

        focused_datapoint.additional_properties = d
        return focused_datapoint

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
