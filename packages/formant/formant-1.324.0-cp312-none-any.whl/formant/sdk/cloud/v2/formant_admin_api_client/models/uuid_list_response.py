from typing import Any, Dict, List, Type, TypeVar, cast

import attr

T = TypeVar("T", bound="UuidListResponse")

@attr.s(auto_attribs=True)
class UuidListResponse:
    """
    Attributes:
        items (List[str]):
    """

    items: List[str]
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        items = self.items





        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "items": items,
        })

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        items = cast(List[str], d.pop("items"))


        uuid_list_response = cls(
            items=items,
        )

        uuid_list_response.additional_properties = d
        return uuid_list_response

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
