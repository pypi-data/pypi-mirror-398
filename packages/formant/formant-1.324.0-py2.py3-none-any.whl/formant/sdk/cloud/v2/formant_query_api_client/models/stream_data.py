from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar

import attr

from ..models.stream_data_type import StreamDataType

if TYPE_CHECKING:
    from ..models.stream_data_points_item import StreamDataPointsItem
    from ..models.stream_data_tags import StreamDataTags


T = TypeVar("T", bound="StreamData")


@attr.s(auto_attribs=True)
class StreamData:
    """
    Attributes:
        name (str):
        device_id (str):
        tags (StreamDataTags):
        type (StreamDataType):
        points (List['StreamDataPointsItem']):
    """

    name: str
    device_id: str
    tags: "StreamDataTags"
    type: StreamDataType
    points: List["StreamDataPointsItem"]
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        name = self.name
        device_id = self.device_id
        tags = self.tags.to_dict()

        type = self.type.value

        points = []
        for points_item_data in self.points:
            points_item = points_item_data.to_dict()

            points.append(points_item)

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "deviceId": device_id,
                "tags": tags,
                "type": type,
                "points": points,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.stream_data_points_item import StreamDataPointsItem
        from ..models.stream_data_tags import StreamDataTags

        d = src_dict.copy()
        name = d.pop("name")

        device_id = d.pop("deviceId")

        tags = StreamDataTags.from_dict(d.pop("tags"))

        type = StreamDataType(d.pop("type"))

        points = []
        _points = d.pop("points")
        for points_item_data in _points:
            points_item = StreamDataPointsItem.from_dict(
                type=type, raw_data=points_item_data
            )

            points.append(points_item)

        stream_data = cls(
            name=name,
            device_id=device_id,
            tags=tags,
            type=type,
            points=points,
        )

        stream_data.additional_properties = d
        return stream_data

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
