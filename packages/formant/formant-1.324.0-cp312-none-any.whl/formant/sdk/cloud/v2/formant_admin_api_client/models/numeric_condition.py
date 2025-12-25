from typing import Any, Dict, List, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

T = TypeVar("T", bound="NumericCondition")

@attr.s(auto_attribs=True)
class NumericCondition:
    """
    Attributes:
        label (str):
        threshold (Union[Unset, Any]):
    """

    label: str
    threshold: Union[Unset, Any] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        label = self.label
        threshold = self.threshold

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "label": label,
        })
        if threshold is not UNSET:
            field_dict["threshold"] = threshold

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        label = d.pop("label")

        threshold = d.pop("threshold", UNSET)

        numeric_condition = cls(
            label=label,
            threshold=threshold,
        )

        numeric_condition.additional_properties = d
        return numeric_condition

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
