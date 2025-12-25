from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

if TYPE_CHECKING:
  from ..models.event_trigger import EventTrigger




T = TypeVar("T", bound="UpdatedEventTriggerResponse")

@attr.s(auto_attribs=True)
class UpdatedEventTriggerResponse:
    """
    Attributes:
        event_triggers (Union[Unset, None, List['EventTrigger']]):
        last_updated (Union[Unset, int]):
    """

    event_triggers: Union[Unset, None, List['EventTrigger']] = UNSET
    last_updated: Union[Unset, int] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        event_triggers: Union[Unset, None, List[Dict[str, Any]]] = UNSET
        if not isinstance(self.event_triggers, Unset):
            if self.event_triggers is None:
                event_triggers = None
            else:
                event_triggers = []
                for event_triggers_item_data in self.event_triggers:
                    event_triggers_item = event_triggers_item_data.to_dict()

                    event_triggers.append(event_triggers_item)




        last_updated = self.last_updated

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
        })
        if event_triggers is not UNSET:
            field_dict["eventTriggers"] = event_triggers
        if last_updated is not UNSET:
            field_dict["lastUpdated"] = last_updated

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.event_trigger import EventTrigger
        d = src_dict.copy()
        event_triggers = []
        _event_triggers = d.pop("eventTriggers", UNSET)
        for event_triggers_item_data in (_event_triggers or []):
            event_triggers_item = EventTrigger.from_dict(event_triggers_item_data)



            event_triggers.append(event_triggers_item)


        last_updated = d.pop("lastUpdated", UNSET)

        updated_event_trigger_response = cls(
            event_triggers=event_triggers,
            last_updated=last_updated,
        )

        updated_event_trigger_response.additional_properties = d
        return updated_event_trigger_response

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
