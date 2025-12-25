from typing import Any, Dict, List, Type, TypeVar, Union, cast

import attr

from ..types import UNSET, Unset

T = TypeVar("T", bound="SchedulesQuery")

@attr.s(auto_attribs=True)
class SchedulesQuery:
    """
    Attributes:
        organization_id (Union[Unset, List[str]]):
        active (Union[Unset, bool]):
    """

    organization_id: Union[Unset, List[str]] = UNSET
    active: Union[Unset, bool] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        organization_id: Union[Unset, List[str]] = UNSET
        if not isinstance(self.organization_id, Unset):
            organization_id = self.organization_id




        active = self.active

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
        })
        if organization_id is not UNSET:
            field_dict["organizationId"] = organization_id
        if active is not UNSET:
            field_dict["active"] = active

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        organization_id = cast(List[str], d.pop("organizationId", UNSET))


        active = d.pop("active", UNSET)

        schedules_query = cls(
            organization_id=organization_id,
            active=active,
        )

        schedules_query.additional_properties = d
        return schedules_query

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
