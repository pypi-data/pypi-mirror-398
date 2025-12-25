from typing import Any, Dict, List, Type, TypeVar

import attr

T = TypeVar("T", bound="TeleopRequestData")

@attr.s(auto_attribs=True)
class TeleopRequestData:
    """
    Attributes:
        instruction (str):
    """

    instruction: str
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        instruction = self.instruction

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "instruction": instruction,
        })

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        instruction = d.pop("instruction")

        teleop_request_data = cls(
            instruction=instruction,
        )

        teleop_request_data.additional_properties = d
        return teleop_request_data

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
