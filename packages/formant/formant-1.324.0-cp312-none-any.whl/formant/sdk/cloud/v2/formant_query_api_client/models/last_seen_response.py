import datetime
from typing import Any, Dict, List, Type, TypeVar

import attr
from dateutil.parser import isoparse

T = TypeVar("T", bound="LastSeenResponse")

@attr.s(auto_attribs=True)
class LastSeenResponse:
    """
    Attributes:
        organization_id (str):
        device_id (str):
        time (datetime.datetime):
    """

    organization_id: str
    device_id: str
    time: datetime.datetime
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        organization_id = self.organization_id
        device_id = self.device_id
        time = self.time.isoformat()


        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "organizationId": organization_id,
            "deviceId": device_id,
            "time": time,
        })

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        organization_id = d.pop("organizationId")

        device_id = d.pop("deviceId")

        time = isoparse(d.pop("time"))




        last_seen_response = cls(
            organization_id=organization_id,
            device_id=device_id,
            time=time,
        )

        last_seen_response.additional_properties = d
        return last_seen_response

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
