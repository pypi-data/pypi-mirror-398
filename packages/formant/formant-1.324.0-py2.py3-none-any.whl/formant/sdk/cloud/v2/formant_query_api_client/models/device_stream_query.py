from typing import Any, Dict, List, Type, TypeVar, Union, cast

import attr

from ..models.device_stream_query_sort_order import DeviceStreamQuerySortOrder
from ..types import UNSET, Unset

T = TypeVar("T", bound="DeviceStreamQuery")

@attr.s(auto_attribs=True)
class DeviceStreamQuery:
    """
    Attributes:
        stream_names (List[str]):
        online (Union[Unset, bool]):
        sort_column (Union[Unset, str]):
        sort_order (Union[Unset, DeviceStreamQuerySortOrder]):
        limit (Union[Unset, int]):
        offset (Union[Unset, int]):
    """

    stream_names: List[str]
    online: Union[Unset, bool] = UNSET
    sort_column: Union[Unset, str] = UNSET
    sort_order: Union[Unset, DeviceStreamQuerySortOrder] = UNSET
    limit: Union[Unset, int] = UNSET
    offset: Union[Unset, int] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        stream_names = self.stream_names




        online = self.online
        sort_column = self.sort_column
        sort_order: Union[Unset, str] = UNSET
        if not isinstance(self.sort_order, Unset):
            sort_order = self.sort_order.value

        limit = self.limit
        offset = self.offset

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "streamNames": stream_names,
        })
        if online is not UNSET:
            field_dict["online"] = online
        if sort_column is not UNSET:
            field_dict["sortColumn"] = sort_column
        if sort_order is not UNSET:
            field_dict["sortOrder"] = sort_order
        if limit is not UNSET:
            field_dict["limit"] = limit
        if offset is not UNSET:
            field_dict["offset"] = offset

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        stream_names = cast(List[str], d.pop("streamNames"))


        online = d.pop("online", UNSET)

        sort_column = d.pop("sortColumn", UNSET)

        _sort_order = d.pop("sortOrder", UNSET)
        sort_order: Union[Unset, DeviceStreamQuerySortOrder]
        if isinstance(_sort_order,  Unset):
            sort_order = UNSET
        else:
            sort_order = DeviceStreamQuerySortOrder(_sort_order)




        limit = d.pop("limit", UNSET)

        offset = d.pop("offset", UNSET)

        device_stream_query = cls(
            stream_names=stream_names,
            online=online,
            sort_column=sort_column,
            sort_order=sort_order,
            limit=limit,
            offset=offset,
        )

        device_stream_query.additional_properties = d
        return device_stream_query

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
