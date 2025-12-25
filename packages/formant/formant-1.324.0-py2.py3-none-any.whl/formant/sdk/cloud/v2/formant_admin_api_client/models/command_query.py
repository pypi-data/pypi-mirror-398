import datetime
from typing import Any, Dict, List, Type, TypeVar, Union

import attr
from dateutil.parser import isoparse

from ..models.command_query_destination import CommandQueryDestination
from ..types import UNSET, Unset

T = TypeVar("T", bound="CommandQuery")

@attr.s(auto_attribs=True)
class CommandQuery:
    """
    Attributes:
        organization_id (Union[Unset, str]):
        device_id (Union[Unset, str]):
        created_after (Union[Unset, datetime.datetime]):
        limit (Union[Unset, int]):
        destination (Union[Unset, CommandQueryDestination]):
        next_ (Union[Unset, Any]):
    """

    organization_id: Union[Unset, str] = UNSET
    device_id: Union[Unset, str] = UNSET
    created_after: Union[Unset, datetime.datetime] = UNSET
    limit: Union[Unset, int] = UNSET
    destination: Union[Unset, CommandQueryDestination] = UNSET
    next_: Union[Unset, Any] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        organization_id = self.organization_id
        device_id = self.device_id
        created_after: Union[Unset, str] = UNSET
        if not isinstance(self.created_after, Unset):
            created_after = self.created_after.isoformat()

        limit = self.limit
        destination: Union[Unset, str] = UNSET
        if not isinstance(self.destination, Unset):
            destination = self.destination.value

        next_ = self.next_

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
        })
        if organization_id is not UNSET:
            field_dict["organizationId"] = organization_id
        if device_id is not UNSET:
            field_dict["deviceId"] = device_id
        if created_after is not UNSET:
            field_dict["createdAfter"] = created_after
        if limit is not UNSET:
            field_dict["limit"] = limit
        if destination is not UNSET:
            field_dict["destination"] = destination
        if next_ is not UNSET:
            field_dict["next"] = next_

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        organization_id = d.pop("organizationId", UNSET)

        device_id = d.pop("deviceId", UNSET)

        _created_after = d.pop("createdAfter", UNSET)
        created_after: Union[Unset, datetime.datetime]
        if isinstance(_created_after,  Unset):
            created_after = UNSET
        else:
            created_after = isoparse(_created_after)




        limit = d.pop("limit", UNSET)

        _destination = d.pop("destination", UNSET)
        destination: Union[Unset, CommandQueryDestination]
        if isinstance(_destination,  Unset):
            destination = UNSET
        else:
            destination = CommandQueryDestination(_destination)




        next_ = d.pop("next", UNSET)

        command_query = cls(
            organization_id=organization_id,
            device_id=device_id,
            created_after=created_after,
            limit=limit,
            destination=destination,
            next_=next_,
        )

        command_query.additional_properties = d
        return command_query

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
