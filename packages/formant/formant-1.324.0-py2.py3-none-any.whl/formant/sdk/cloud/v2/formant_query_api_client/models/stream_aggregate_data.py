from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar

import attr

from ..models.stream_aggregate_data_type import StreamAggregateDataType

if TYPE_CHECKING:
  from ..models.stream_aggregate_data_tags import StreamAggregateDataTags




T = TypeVar("T", bound="StreamAggregateData")

@attr.s(auto_attribs=True)
class StreamAggregateData:
    """
    Attributes:
        name (str):
        device_id (str):
        tags (StreamAggregateDataTags):
        type (StreamAggregateDataType):
        aggregates (Any):
    """

    name: str
    device_id: str
    tags: 'StreamAggregateDataTags'
    type: StreamAggregateDataType
    aggregates: Any
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        name = self.name
        device_id = self.device_id
        tags = self.tags.to_dict()

        type = self.type.value

        aggregates = self.aggregates

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "name": name,
            "deviceId": device_id,
            "tags": tags,
            "type": type,
            "aggregates": aggregates,
        })

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.stream_aggregate_data_tags import StreamAggregateDataTags
        d = src_dict.copy()
        name = d.pop("name")

        device_id = d.pop("deviceId")

        tags = StreamAggregateDataTags.from_dict(d.pop("tags"))




        type = StreamAggregateDataType(d.pop("type"))




        aggregates = d.pop("aggregates")

        stream_aggregate_data = cls(
            name=name,
            device_id=device_id,
            tags=tags,
            type=type,
            aggregates=aggregates,
        )

        stream_aggregate_data.additional_properties = d
        return stream_aggregate_data

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
