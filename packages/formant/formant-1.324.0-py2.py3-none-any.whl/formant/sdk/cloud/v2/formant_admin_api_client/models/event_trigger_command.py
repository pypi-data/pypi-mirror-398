from typing import Any, Dict, List, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

T = TypeVar("T", bound="EventTriggerCommand")

@attr.s(auto_attribs=True)
class EventTriggerCommand:
    """
    Attributes:
        command_template_id (str):
        parameter_value (Union[Unset, str]):
    """

    command_template_id: str
    parameter_value: Union[Unset, str] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        command_template_id = self.command_template_id
        parameter_value = self.parameter_value

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "commandTemplateId": command_template_id,
        })
        if parameter_value is not UNSET:
            field_dict["parameterValue"] = parameter_value

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        command_template_id = d.pop("commandTemplateId")

        parameter_value = d.pop("parameterValue", UNSET)

        event_trigger_command = cls(
            command_template_id=command_template_id,
            parameter_value=parameter_value,
        )

        event_trigger_command.additional_properties = d
        return event_trigger_command

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
