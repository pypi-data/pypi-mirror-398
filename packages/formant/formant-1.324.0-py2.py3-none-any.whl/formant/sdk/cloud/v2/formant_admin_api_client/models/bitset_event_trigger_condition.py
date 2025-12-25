from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar

import attr

from ..models.bitset_event_trigger_condition_operator import \
    BitsetEventTriggerConditionOperator
from ..models.bitset_event_trigger_condition_type import \
    BitsetEventTriggerConditionType

if TYPE_CHECKING:
  from ..models.bit_condition import BitCondition




T = TypeVar("T", bound="BitsetEventTriggerCondition")

@attr.s(auto_attribs=True)
class BitsetEventTriggerCondition:
    """
    Attributes:
        type (BitsetEventTriggerConditionType):
        bit_conditions (List['BitCondition']):
        operator (BitsetEventTriggerConditionOperator):
        stream (str):
    """

    type: BitsetEventTriggerConditionType
    bit_conditions: List['BitCondition']
    operator: BitsetEventTriggerConditionOperator
    stream: str
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        type = self.type.value

        bit_conditions = []
        for bit_conditions_item_data in self.bit_conditions:
            bit_conditions_item = bit_conditions_item_data.to_dict()

            bit_conditions.append(bit_conditions_item)




        operator = self.operator.value

        stream = self.stream

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "type": type,
            "bitConditions": bit_conditions,
            "operator": operator,
            "stream": stream,
        })

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.bit_condition import BitCondition
        d = src_dict.copy()
        type = BitsetEventTriggerConditionType(d.pop("type"))




        bit_conditions = []
        _bit_conditions = d.pop("bitConditions")
        for bit_conditions_item_data in (_bit_conditions):
            bit_conditions_item = BitCondition.from_dict(bit_conditions_item_data)



            bit_conditions.append(bit_conditions_item)


        operator = BitsetEventTriggerConditionOperator(d.pop("operator"))




        stream = d.pop("stream")

        bitset_event_trigger_condition = cls(
            type=type,
            bit_conditions=bit_conditions,
            operator=operator,
            stream=stream,
        )

        bitset_event_trigger_condition.additional_properties = d
        return bitset_event_trigger_condition

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
