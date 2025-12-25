from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

if TYPE_CHECKING:
  from ..models.custom_event import CustomEvent




T = TypeVar("T", bound="CustomEventBatchRequest")

@attr.s(auto_attribs=True)
class CustomEventBatchRequest:
    """
    Attributes:
        items (List['CustomEvent']):
        ignore_duplicates (Union[Unset, bool]):
        without_device_tags (Union[Unset, bool]):
    """

    items: List['CustomEvent']
    ignore_duplicates: Union[Unset, bool] = UNSET
    without_device_tags: Union[Unset, bool] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        items = []
        for items_item_data in self.items:
            items_item = items_item_data.to_dict()

            items.append(items_item)




        ignore_duplicates = self.ignore_duplicates
        without_device_tags = self.without_device_tags

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "items": items,
        })
        if ignore_duplicates is not UNSET:
            field_dict["ignoreDuplicates"] = ignore_duplicates
        if without_device_tags is not UNSET:
            field_dict["withoutDeviceTags"] = without_device_tags

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.custom_event import CustomEvent
        d = src_dict.copy()
        items = []
        _items = d.pop("items")
        for items_item_data in (_items):
            items_item = CustomEvent.from_dict(items_item_data)



            items.append(items_item)


        ignore_duplicates = d.pop("ignoreDuplicates", UNSET)

        without_device_tags = d.pop("withoutDeviceTags", UNSET)

        custom_event_batch_request = cls(
            items=items,
            ignore_duplicates=ignore_duplicates,
            without_device_tags=without_device_tags,
        )

        custom_event_batch_request.additional_properties = d
        return custom_event_batch_request

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
