from typing import Any, Dict, List, Type, TypeVar

import attr

from ..models.regex_event_trigger_condition_type import \
    RegexEventTriggerConditionType

T = TypeVar("T", bound="RegexEventTriggerCondition")

@attr.s(auto_attribs=True)
class RegexEventTriggerCondition:
    """
    Attributes:
        type (RegexEventTriggerConditionType):
        value (str):
        stream (str):
    """

    type: RegexEventTriggerConditionType
    value: str
    stream: str
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        type = self.type.value

        value = self.value
        stream = self.stream

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "type": type,
            "value": value,
            "stream": stream,
        })

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        type = RegexEventTriggerConditionType(d.pop("type"))




        value = d.pop("value")

        stream = d.pop("stream")

        regex_event_trigger_condition = cls(
            type=type,
            value=value,
            stream=stream,
        )

        regex_event_trigger_condition.additional_properties = d
        return regex_event_trigger_condition

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
