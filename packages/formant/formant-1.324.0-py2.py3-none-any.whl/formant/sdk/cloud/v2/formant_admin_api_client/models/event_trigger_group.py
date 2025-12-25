import datetime
from typing import (TYPE_CHECKING, Any, Dict, List, Optional, Type, TypeVar,
                    Union, cast)

import attr
from dateutil.parser import isoparse

from ..types import UNSET, Unset

if TYPE_CHECKING:
  from ..models.event_trigger_group_sms_tags import EventTriggerGroupSmsTags
  from ..models.event_trigger_group_tags import EventTriggerGroupTags
  from ..models.scope_filter import ScopeFilter




T = TypeVar("T", bound="EventTriggerGroup")

@attr.s(auto_attribs=True)
class EventTriggerGroup:
    """
    Attributes:
        sms_tags (EventTriggerGroupSmsTags):
        organization_id (Union[Unset, str]):
        enabled (Union[Unset, bool]):
        device_scope (Optional[ScopeFilter]):
        phone_numbers (Union[Unset, List[str]]): User's phone numbers (e.g., +14155550100).
        id (Union[Unset, str]):
        created_at (Union[Unset, datetime.datetime]):
        updated_at (Union[Unset, datetime.datetime]):
        tags (Union[Unset, EventTriggerGroupTags]):
    """

    sms_tags: 'EventTriggerGroupSmsTags'
    device_scope: Optional['ScopeFilter']
    organization_id: Union[Unset, str] = UNSET
    enabled: Union[Unset, bool] = UNSET
    phone_numbers: Union[Unset, List[str]] = UNSET
    id: Union[Unset, str] = UNSET
    created_at: Union[Unset, datetime.datetime] = UNSET
    updated_at: Union[Unset, datetime.datetime] = UNSET
    tags: Union[Unset, 'EventTriggerGroupTags'] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        sms_tags = self.sms_tags.to_dict()

        organization_id = self.organization_id
        enabled = self.enabled
        device_scope = self.device_scope.to_dict() if self.device_scope else None

        phone_numbers: Union[Unset, List[str]] = UNSET
        if not isinstance(self.phone_numbers, Unset):
            phone_numbers = self.phone_numbers




        id = self.id
        created_at: Union[Unset, str] = UNSET
        if not isinstance(self.created_at, Unset):
            created_at = self.created_at.isoformat()

        updated_at: Union[Unset, str] = UNSET
        if not isinstance(self.updated_at, Unset):
            updated_at = self.updated_at.isoformat()

        tags: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.tags, Unset):
            tags = self.tags.to_dict()


        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "smsTags": sms_tags,
            "deviceScope": device_scope,
        })
        if organization_id is not UNSET:
            field_dict["organizationId"] = organization_id
        if enabled is not UNSET:
            field_dict["enabled"] = enabled
        if phone_numbers is not UNSET:
            field_dict["phoneNumbers"] = phone_numbers
        if id is not UNSET:
            field_dict["id"] = id
        if created_at is not UNSET:
            field_dict["createdAt"] = created_at
        if updated_at is not UNSET:
            field_dict["updatedAt"] = updated_at
        if tags is not UNSET:
            field_dict["tags"] = tags

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.event_trigger_group_sms_tags import \
            EventTriggerGroupSmsTags
        from ..models.event_trigger_group_tags import EventTriggerGroupTags
        from ..models.scope_filter import ScopeFilter
        d = src_dict.copy()
        sms_tags = EventTriggerGroupSmsTags.from_dict(d.pop("smsTags"))




        organization_id = d.pop("organizationId", UNSET)

        enabled = d.pop("enabled", UNSET)

        _device_scope = d.pop("deviceScope")
        device_scope: Optional[ScopeFilter]
        if _device_scope is None:
            device_scope = None
        else:
            device_scope = ScopeFilter.from_dict(_device_scope)




        phone_numbers = cast(List[str], d.pop("phoneNumbers", UNSET))


        id = d.pop("id", UNSET)

        _created_at = d.pop("createdAt", UNSET)
        created_at: Union[Unset, datetime.datetime]
        if isinstance(_created_at,  Unset):
            created_at = UNSET
        else:
            created_at = isoparse(_created_at)




        _updated_at = d.pop("updatedAt", UNSET)
        updated_at: Union[Unset, datetime.datetime]
        if isinstance(_updated_at,  Unset):
            updated_at = UNSET
        else:
            updated_at = isoparse(_updated_at)




        _tags = d.pop("tags", UNSET)
        tags: Union[Unset, EventTriggerGroupTags]
        if isinstance(_tags,  Unset):
            tags = UNSET
        else:
            tags = EventTriggerGroupTags.from_dict(_tags)




        event_trigger_group = cls(
            sms_tags=sms_tags,
            organization_id=organization_id,
            enabled=enabled,
            device_scope=device_scope,
            phone_numbers=phone_numbers,
            id=id,
            created_at=created_at,
            updated_at=updated_at,
            tags=tags,
        )

        event_trigger_group.additional_properties = d
        return event_trigger_group

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
