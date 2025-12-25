import datetime
from typing import Any, Dict, List, Type, TypeVar, Union

import attr
from dateutil.parser import isoparse

from ..types import UNSET, Unset

T = TypeVar("T", bound="PhysicalRequestData")

@attr.s(auto_attribs=True)
class PhysicalRequestData:
    """
    Attributes:
        reason (str):
        metadata (Union[Unset, Any]):
        start_time (Union[Unset, datetime.datetime]):
        end_time (Union[Unset, datetime.datetime]):
    """

    reason: str
    metadata: Union[Unset, Any] = UNSET
    start_time: Union[Unset, datetime.datetime] = UNSET
    end_time: Union[Unset, datetime.datetime] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        reason = self.reason
        metadata = self.metadata
        start_time: Union[Unset, str] = UNSET
        if not isinstance(self.start_time, Unset):
            start_time = self.start_time.isoformat()

        end_time: Union[Unset, str] = UNSET
        if not isinstance(self.end_time, Unset):
            end_time = self.end_time.isoformat()


        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "reason": reason,
        })
        if metadata is not UNSET:
            field_dict["metadata"] = metadata
        if start_time is not UNSET:
            field_dict["startTime"] = start_time
        if end_time is not UNSET:
            field_dict["endTime"] = end_time

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        reason = d.pop("reason")

        metadata = d.pop("metadata", UNSET)

        _start_time = d.pop("startTime", UNSET)
        start_time: Union[Unset, datetime.datetime]
        if isinstance(_start_time,  Unset):
            start_time = UNSET
        else:
            start_time = isoparse(_start_time)




        _end_time = d.pop("endTime", UNSET)
        end_time: Union[Unset, datetime.datetime]
        if isinstance(_end_time,  Unset):
            end_time = UNSET
        else:
            end_time = isoparse(_end_time)




        physical_request_data = cls(
            reason=reason,
            metadata=metadata,
            start_time=start_time,
            end_time=end_time,
        )

        physical_request_data.additional_properties = d
        return physical_request_data

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
