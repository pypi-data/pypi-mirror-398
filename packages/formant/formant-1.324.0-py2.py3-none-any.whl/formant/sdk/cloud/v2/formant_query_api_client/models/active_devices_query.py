import datetime
from typing import Any, Dict, List, Type, TypeVar, Union

import attr
from dateutil.parser import isoparse

from ..models.active_devices_query_type import ActiveDevicesQueryType
from ..types import UNSET, Unset

T = TypeVar("T", bound="ActiveDevicesQuery")

@attr.s(auto_attribs=True)
class ActiveDevicesQuery:
    """
    Attributes:
        start (datetime.datetime):
        end (datetime.datetime):
        organization_id (Union[Unset, str]):
        type (Union[Unset, ActiveDevicesQueryType]):
    """

    start: datetime.datetime
    end: datetime.datetime
    organization_id: Union[Unset, str] = UNSET
    type: Union[Unset, ActiveDevicesQueryType] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        start = self.start.isoformat()

        end = self.end.isoformat()

        organization_id = self.organization_id
        type: Union[Unset, str] = UNSET
        if not isinstance(self.type, Unset):
            type = self.type.value


        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "start": start,
            "end": end,
        })
        if organization_id is not UNSET:
            field_dict["organizationId"] = organization_id
        if type is not UNSET:
            field_dict["type"] = type

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        start = isoparse(d.pop("start"))




        end = isoparse(d.pop("end"))




        organization_id = d.pop("organizationId", UNSET)

        _type = d.pop("type", UNSET)
        type: Union[Unset, ActiveDevicesQueryType]
        if isinstance(_type,  Unset):
            type = UNSET
        else:
            type = ActiveDevicesQueryType(_type)




        active_devices_query = cls(
            start=start,
            end=end,
            organization_id=organization_id,
            type=type,
        )

        active_devices_query.additional_properties = d
        return active_devices_query

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
