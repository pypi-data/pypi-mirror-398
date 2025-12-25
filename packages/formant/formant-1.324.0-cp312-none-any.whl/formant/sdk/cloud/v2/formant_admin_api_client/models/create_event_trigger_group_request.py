from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union, cast

import attr

from ..types import UNSET, Unset

if TYPE_CHECKING:
  from ..models.create_event_trigger_group_request_tags import \
      CreateEventTriggerGroupRequestTags
  from ..models.event_trigger import EventTrigger




T = TypeVar("T", bound="CreateEventTriggerGroupRequest")

@attr.s(auto_attribs=True)
class CreateEventTriggerGroupRequest:
    """
    Attributes:
        phone_numbers (List[str]):
        device_ids (List[str]):
        event_triggers (EventTrigger):
        tags (Union[Unset, CreateEventTriggerGroupRequestTags]):
        is_already_opted_in (Union[Unset, bool]):
    """

    phone_numbers: List[str]
    device_ids: List[str]
    event_triggers: 'EventTrigger'
    tags: Union[Unset, 'CreateEventTriggerGroupRequestTags'] = UNSET
    is_already_opted_in: Union[Unset, bool] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        phone_numbers = self.phone_numbers




        device_ids = self.device_ids




        event_triggers = self.event_triggers.to_dict()

        tags: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.tags, Unset):
            tags = self.tags.to_dict()

        is_already_opted_in = self.is_already_opted_in

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "phoneNumbers": phone_numbers,
            "deviceIds": device_ids,
            "eventTriggers": event_triggers,
        })
        if tags is not UNSET:
            field_dict["tags"] = tags
        if is_already_opted_in is not UNSET:
            field_dict["isAlreadyOptedIn"] = is_already_opted_in

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.create_event_trigger_group_request_tags import \
            CreateEventTriggerGroupRequestTags
        from ..models.event_trigger import EventTrigger
        d = src_dict.copy()
        phone_numbers = cast(List[str], d.pop("phoneNumbers"))


        device_ids = cast(List[str], d.pop("deviceIds"))


        event_triggers = EventTrigger.from_dict(d.pop("eventTriggers"))




        _tags = d.pop("tags", UNSET)
        tags: Union[Unset, CreateEventTriggerGroupRequestTags]
        if isinstance(_tags,  Unset):
            tags = UNSET
        else:
            tags = CreateEventTriggerGroupRequestTags.from_dict(_tags)




        is_already_opted_in = d.pop("isAlreadyOptedIn", UNSET)

        create_event_trigger_group_request = cls(
            phone_numbers=phone_numbers,
            device_ids=device_ids,
            event_triggers=event_triggers,
            tags=tags,
            is_already_opted_in=is_already_opted_in,
        )

        create_event_trigger_group_request.additional_properties = d
        return create_event_trigger_group_request

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
