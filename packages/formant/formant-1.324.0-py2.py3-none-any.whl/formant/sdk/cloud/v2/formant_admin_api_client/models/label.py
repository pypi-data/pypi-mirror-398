from typing import Any, Dict, List, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

T = TypeVar("T", bound="Label")

@attr.s(auto_attribs=True)
class Label:
    """
    Attributes:
        value (str): Value corresponding to the user-friendly description for this label. This will be passed as the
            response to this intervention request.
        display_name (Union[Unset, str]): User-friendly description of label. This will be presented to the user in a
            dropdown.
        description (Union[Unset, str]):
    """

    value: str
    display_name: Union[Unset, str] = UNSET
    description: Union[Unset, str] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        value = self.value
        display_name = self.display_name
        description = self.description

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "value": value,
        })
        if display_name is not UNSET:
            field_dict["displayName"] = display_name
        if description is not UNSET:
            field_dict["description"] = description

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        value = d.pop("value")

        display_name = d.pop("displayName", UNSET)

        description = d.pop("description", UNSET)

        label = cls(
            value=value,
            display_name=display_name,
            description=description,
        )

        label.additional_properties = d
        return label

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
