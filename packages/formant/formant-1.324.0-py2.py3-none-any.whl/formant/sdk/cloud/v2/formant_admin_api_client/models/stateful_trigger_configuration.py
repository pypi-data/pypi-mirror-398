from typing import Any, Dict, List, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

T = TypeVar("T", bound="StatefulTriggerConfiguration")

@attr.s(auto_attribs=True)
class StatefulTriggerConfiguration:
    """
    Attributes:
        emit_on_entering_state (Union[Unset, bool]):
        emit_on_leaving_state (Union[Unset, bool]):
    """

    emit_on_entering_state: Union[Unset, bool] = UNSET
    emit_on_leaving_state: Union[Unset, bool] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        emit_on_entering_state = self.emit_on_entering_state
        emit_on_leaving_state = self.emit_on_leaving_state

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
        })
        if emit_on_entering_state is not UNSET:
            field_dict["emitOnEnteringState"] = emit_on_entering_state
        if emit_on_leaving_state is not UNSET:
            field_dict["emitOnLeavingState"] = emit_on_leaving_state

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        emit_on_entering_state = d.pop("emitOnEnteringState", UNSET)

        emit_on_leaving_state = d.pop("emitOnLeavingState", UNSET)

        stateful_trigger_configuration = cls(
            emit_on_entering_state=emit_on_entering_state,
            emit_on_leaving_state=emit_on_leaving_state,
        )

        stateful_trigger_configuration.additional_properties = d
        return stateful_trigger_configuration

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
