from typing import Any, Dict, List, Type, TypeVar, Union, cast

import attr

from ..types import UNSET, Unset

T = TypeVar("T", bound="KeyValueQuery")

@attr.s(auto_attribs=True)
class KeyValueQuery:
    """
    Attributes:
        keys (Union[Unset, List[str]]): Array of keys you whose key-value pairs you want to query.
        prefix (Union[Unset, str]): Filters your query to all key-value pairs which start with this string. Case-
            sensitive.
    """

    keys: Union[Unset, List[str]] = UNSET
    prefix: Union[Unset, str] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        keys: Union[Unset, List[str]] = UNSET
        if not isinstance(self.keys, Unset):
            keys = self.keys




        prefix = self.prefix

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
        })
        if keys is not UNSET:
            field_dict["keys"] = keys
        if prefix is not UNSET:
            field_dict["prefix"] = prefix

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        keys = cast(List[str], d.pop("keys", UNSET))


        prefix = d.pop("prefix", UNSET)

        key_value_query = cls(
            keys=keys,
            prefix=prefix,
        )

        key_value_query.additional_properties = d
        return key_value_query

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
