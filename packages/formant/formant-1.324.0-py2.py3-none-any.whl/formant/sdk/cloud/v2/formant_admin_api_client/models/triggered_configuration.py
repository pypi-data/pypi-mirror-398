from typing import Any, Dict, List, Type, TypeVar

import attr

T = TypeVar("T", bound="TriggeredConfiguration")

@attr.s(auto_attribs=True)
class TriggeredConfiguration:
    """
    Attributes:
        configuration_duration_minutes (int):
        configuration_template_id (str):
    """

    configuration_duration_minutes: int
    configuration_template_id: str
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        configuration_duration_minutes = self.configuration_duration_minutes
        configuration_template_id = self.configuration_template_id

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "configurationDurationMinutes": configuration_duration_minutes,
            "configurationTemplateId": configuration_template_id,
        })

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        configuration_duration_minutes = d.pop("configurationDurationMinutes")

        configuration_template_id = d.pop("configurationTemplateId")

        triggered_configuration = cls(
            configuration_duration_minutes=configuration_duration_minutes,
            configuration_template_id=configuration_template_id,
        )

        triggered_configuration.additional_properties = d
        return triggered_configuration

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
