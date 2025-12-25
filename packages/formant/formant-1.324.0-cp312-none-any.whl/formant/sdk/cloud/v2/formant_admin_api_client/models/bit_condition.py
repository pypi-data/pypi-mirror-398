from typing import Any, Dict, List, Type, TypeVar

import attr

T = TypeVar("T", bound="BitCondition")

@attr.s(auto_attribs=True)
class BitCondition:
    """
    Attributes:
        key (str):
        true_ (bool):
        false_ (bool):
    """

    key: str
    true_: bool
    false_: bool
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        key = self.key
        true_ = self.true_
        false_ = self.false_

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "key": key,
            "true": true_,
            "false": false_,
        })

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        key = d.pop("key")

        true_ = d.pop("true")

        false_ = d.pop("false")

        bit_condition = cls(
            key=key,
            true_=true_,
            false_=false_,
        )

        bit_condition.additional_properties = d
        return bit_condition

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
