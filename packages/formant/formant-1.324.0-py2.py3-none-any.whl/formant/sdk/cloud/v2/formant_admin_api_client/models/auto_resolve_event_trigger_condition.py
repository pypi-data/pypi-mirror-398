from typing import Any, Dict, List, Type, TypeVar

import attr

from ..models.auto_resolve_event_trigger_condition_type import \
    AutoResolveEventTriggerConditionType

T = TypeVar("T", bound="AutoResolveEventTriggerCondition")

@attr.s(auto_attribs=True)
class AutoResolveEventTriggerCondition:
    """
    Attributes:
        type (AutoResolveEventTriggerConditionType):
        stream (str):
    """

    type: AutoResolveEventTriggerConditionType
    stream: str
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        type = self.type.value

        stream = self.stream

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "type": type,
            "stream": stream,
        })

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        type = AutoResolveEventTriggerConditionType(d.pop("type"))




        stream = d.pop("stream")

        auto_resolve_event_trigger_condition = cls(
            type=type,
            stream=stream,
        )

        auto_resolve_event_trigger_condition.additional_properties = d
        return auto_resolve_event_trigger_condition

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
