import datetime
from typing import Any, Dict, List, Type, TypeVar, Union

import attr
from dateutil.parser import isoparse

from ..types import UNSET, Unset

T = TypeVar("T", bound="PollCommandRequest")

@attr.s(auto_attribs=True)
class PollCommandRequest:
    """
    Attributes:
        created_at_after (datetime.datetime):
        device_id (Union[Unset, str]):
    """

    created_at_after: datetime.datetime
    device_id: Union[Unset, str] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        created_at_after = self.created_at_after.isoformat()

        device_id = self.device_id

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "createdAtAfter": created_at_after,
        })
        if device_id is not UNSET:
            field_dict["deviceId"] = device_id

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        created_at_after = isoparse(d.pop("createdAtAfter"))




        device_id = d.pop("deviceId", UNSET)

        poll_command_request = cls(
            created_at_after=created_at_after,
            device_id=device_id,
        )

        poll_command_request.additional_properties = d
        return poll_command_request

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
