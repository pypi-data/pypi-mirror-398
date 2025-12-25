import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union, cast

import attr
from dateutil.parser import isoparse

from ..types import UNSET, Unset

if TYPE_CHECKING:
  from ..models.partial_event_trigger_group_sms_tags import \
      PartialEventTriggerGroupSmsTags
  from ..models.partial_event_trigger_group_tags import \
      PartialEventTriggerGroupTags
  from ..models.scope_filter import ScopeFilter




T = TypeVar("T", bound="PartialEventTriggerGroup")

@attr.s(auto_attribs=True)
class PartialEventTriggerGroup:
    """
    Attributes:
        organization_id (Union[Unset, str]):
        enabled (Union[Unset, bool]):
        device_scope (Union[Unset, None, ScopeFilter]):
        sms_tags (Union[Unset, PartialEventTriggerGroupSmsTags]):
        phone_numbers (Union[Unset, List[str]]): User's phone numbers (e.g., +14155550100).
        id (Union[Unset, str]):
        created_at (Union[Unset, datetime.datetime]):
        updated_at (Union[Unset, datetime.datetime]):
        tags (Union[Unset, PartialEventTriggerGroupTags]):
    """

    organization_id: Union[Unset, str] = UNSET
    enabled: Union[Unset, bool] = UNSET
    device_scope: Union[Unset, None, 'ScopeFilter'] = UNSET
    sms_tags: Union[Unset, 'PartialEventTriggerGroupSmsTags'] = UNSET
    phone_numbers: Union[Unset, List[str]] = UNSET
    id: Union[Unset, str] = UNSET
    created_at: Union[Unset, datetime.datetime] = UNSET
    updated_at: Union[Unset, datetime.datetime] = UNSET
    tags: Union[Unset, 'PartialEventTriggerGroupTags'] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        organization_id = self.organization_id
        enabled = self.enabled
        device_scope: Union[Unset, None, Dict[str, Any]] = UNSET
        if not isinstance(self.device_scope, Unset):
            device_scope = self.device_scope.to_dict() if self.device_scope else None

        sms_tags: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.sms_tags, Unset):
            sms_tags = self.sms_tags.to_dict()

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
        })
        if organization_id is not UNSET:
            field_dict["organizationId"] = organization_id
        if enabled is not UNSET:
            field_dict["enabled"] = enabled
        if device_scope is not UNSET:
            field_dict["deviceScope"] = device_scope
        if sms_tags is not UNSET:
            field_dict["smsTags"] = sms_tags
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
        from ..models.partial_event_trigger_group_sms_tags import \
            PartialEventTriggerGroupSmsTags
        from ..models.partial_event_trigger_group_tags import \
            PartialEventTriggerGroupTags
        from ..models.scope_filter import ScopeFilter
        d = src_dict.copy()
        organization_id = d.pop("organizationId", UNSET)

        enabled = d.pop("enabled", UNSET)

        _device_scope = d.pop("deviceScope", UNSET)
        device_scope: Union[Unset, None, ScopeFilter]
        if _device_scope is None:
            device_scope = None
        elif isinstance(_device_scope,  Unset):
            device_scope = UNSET
        else:
            device_scope = ScopeFilter.from_dict(_device_scope)




        _sms_tags = d.pop("smsTags", UNSET)
        sms_tags: Union[Unset, PartialEventTriggerGroupSmsTags]
        if isinstance(_sms_tags,  Unset):
            sms_tags = UNSET
        else:
            sms_tags = PartialEventTriggerGroupSmsTags.from_dict(_sms_tags)




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
        tags: Union[Unset, PartialEventTriggerGroupTags]
        if isinstance(_tags,  Unset):
            tags = UNSET
        else:
            tags = PartialEventTriggerGroupTags.from_dict(_tags)




        partial_event_trigger_group = cls(
            organization_id=organization_id,
            enabled=enabled,
            device_scope=device_scope,
            sms_tags=sms_tags,
            phone_numbers=phone_numbers,
            id=id,
            created_at=created_at,
            updated_at=updated_at,
            tags=tags,
        )

        partial_event_trigger_group.additional_properties = d
        return partial_event_trigger_group

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
