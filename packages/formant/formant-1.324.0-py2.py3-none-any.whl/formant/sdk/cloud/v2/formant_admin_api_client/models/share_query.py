from typing import Any, Dict, List, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

T = TypeVar("T", bound="ShareQuery")

@attr.s(auto_attribs=True)
class ShareQuery:
    """
    Attributes:
        has_module (Union[Unset, bool]): Query for shared tokens for modules.
        count (Union[Unset, float]): Limit the number of share tokens returned by this query.
        offset (Union[Unset, float]): Paginate the results by specifying an offset.
    """

    has_module: Union[Unset, bool] = UNSET
    count: Union[Unset, float] = UNSET
    offset: Union[Unset, float] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        has_module = self.has_module
        count = self.count
        offset = self.offset

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
        })
        if has_module is not UNSET:
            field_dict["hasModule"] = has_module
        if count is not UNSET:
            field_dict["count"] = count
        if offset is not UNSET:
            field_dict["offset"] = offset

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        has_module = d.pop("hasModule", UNSET)

        count = d.pop("count", UNSET)

        offset = d.pop("offset", UNSET)

        share_query = cls(
            has_module=has_module,
            count=count,
            offset=offset,
        )

        share_query.additional_properties = d
        return share_query

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
