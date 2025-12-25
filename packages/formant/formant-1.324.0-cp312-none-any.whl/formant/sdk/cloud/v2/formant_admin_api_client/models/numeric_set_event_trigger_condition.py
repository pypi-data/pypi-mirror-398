from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar

import attr

from ..models.numeric_set_event_trigger_condition_operator import \
    NumericSetEventTriggerConditionOperator
from ..models.numeric_set_event_trigger_condition_type import \
    NumericSetEventTriggerConditionType

if TYPE_CHECKING:
  from ..models.numeric_condition import NumericCondition




T = TypeVar("T", bound="NumericSetEventTriggerCondition")

@attr.s(auto_attribs=True)
class NumericSetEventTriggerCondition:
    """
    Attributes:
        type (NumericSetEventTriggerConditionType):
        conditions (List['NumericCondition']):
        operator (NumericSetEventTriggerConditionOperator):
        stream (str):
    """

    type: NumericSetEventTriggerConditionType
    conditions: List['NumericCondition']
    operator: NumericSetEventTriggerConditionOperator
    stream: str
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        type = self.type.value

        conditions = []
        for conditions_item_data in self.conditions:
            conditions_item = conditions_item_data.to_dict()

            conditions.append(conditions_item)




        operator = self.operator.value

        stream = self.stream

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "type": type,
            "conditions": conditions,
            "operator": operator,
            "stream": stream,
        })

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.numeric_condition import NumericCondition
        d = src_dict.copy()
        type = NumericSetEventTriggerConditionType(d.pop("type"))




        conditions = []
        _conditions = d.pop("conditions")
        for conditions_item_data in (_conditions):
            conditions_item = NumericCondition.from_dict(conditions_item_data)



            conditions.append(conditions_item)


        operator = NumericSetEventTriggerConditionOperator(d.pop("operator"))




        stream = d.pop("stream")

        numeric_set_event_trigger_condition = cls(
            type=type,
            conditions=conditions,
            operator=operator,
            stream=stream,
        )

        numeric_set_event_trigger_condition.additional_properties = d
        return numeric_set_event_trigger_condition

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
