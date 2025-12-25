from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar

import attr

from ..models.battery_event_trigger_condition_operator import \
    BatteryEventTriggerConditionOperator
from ..models.battery_event_trigger_condition_type import \
    BatteryEventTriggerConditionType

if TYPE_CHECKING:
  from ..models.battery_event_trigger_condition_conditions import \
      BatteryEventTriggerConditionConditions




T = TypeVar("T", bound="BatteryEventTriggerCondition")

@attr.s(auto_attribs=True)
class BatteryEventTriggerCondition:
    """
    Attributes:
        type (BatteryEventTriggerConditionType):
        conditions (BatteryEventTriggerConditionConditions):
        operator (BatteryEventTriggerConditionOperator):
        stream (str):
    """

    type: BatteryEventTriggerConditionType
    conditions: 'BatteryEventTriggerConditionConditions'
    operator: BatteryEventTriggerConditionOperator
    stream: str
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        type = self.type.value

        conditions = self.conditions.to_dict()

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
        from ..models.battery_event_trigger_condition_conditions import \
            BatteryEventTriggerConditionConditions
        d = src_dict.copy()
        type = BatteryEventTriggerConditionType(d.pop("type"))




        conditions = BatteryEventTriggerConditionConditions.from_dict(d.pop("conditions"))




        operator = BatteryEventTriggerConditionOperator(d.pop("operator"))




        stream = d.pop("stream")

        battery_event_trigger_condition = cls(
            type=type,
            conditions=conditions,
            operator=operator,
            stream=stream,
        )

        battery_event_trigger_condition.additional_properties = d
        return battery_event_trigger_condition

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
