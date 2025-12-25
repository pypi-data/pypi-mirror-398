from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

if TYPE_CHECKING:
  from ..models.stream_aggregate_data import StreamAggregateData
  from ..models.stream_data import StreamData




T = TypeVar("T", bound="StreamDataListResponse")

@attr.s(auto_attribs=True)
class StreamDataListResponse:
    """
    Attributes:
        items (List['StreamData']):
        aggregates (Union[Unset, List['StreamAggregateData']]):
        next_ (Union[Unset, Any]):
    """

    items: List['StreamData']
    aggregates: Union[Unset, List['StreamAggregateData']] = UNSET
    next_: Union[Unset, Any] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        items = []
        for items_item_data in self.items:
            items_item = items_item_data.to_dict()

            items.append(items_item)




        aggregates: Union[Unset, List[Dict[str, Any]]] = UNSET
        if not isinstance(self.aggregates, Unset):
            aggregates = []
            for aggregates_item_data in self.aggregates:
                aggregates_item = aggregates_item_data.to_dict()

                aggregates.append(aggregates_item)




        next_ = self.next_

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "items": items,
        })
        if aggregates is not UNSET:
            field_dict["aggregates"] = aggregates
        if next_ is not UNSET:
            field_dict["next"] = next_

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.stream_aggregate_data import StreamAggregateData
        from ..models.stream_data import StreamData
        d = src_dict.copy()
        items = []
        _items = d.pop("items")
        for items_item_data in (_items):
            items_item = StreamData.from_dict(items_item_data)



            items.append(items_item)


        aggregates = []
        _aggregates = d.pop("aggregates", UNSET)
        for aggregates_item_data in (_aggregates or []):
            aggregates_item = StreamAggregateData.from_dict(aggregates_item_data)



            aggregates.append(aggregates_item)


        next_ = d.pop("next", UNSET)

        stream_data_list_response = cls(
            items=items,
            aggregates=aggregates,
            next_=next_,
        )

        stream_data_list_response.additional_properties = d
        return stream_data_list_response

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
