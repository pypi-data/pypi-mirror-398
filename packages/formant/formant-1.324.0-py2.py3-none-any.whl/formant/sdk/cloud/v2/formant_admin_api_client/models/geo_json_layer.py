from typing import Any, Dict, List, Type, TypeVar

import attr

T = TypeVar("T", bound="GeoJsonLayer")

@attr.s(auto_attribs=True)
class GeoJsonLayer:
    """
    Attributes:
        stream_id (str):
    """

    stream_id: str
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        stream_id = self.stream_id

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "streamId": stream_id,
        })

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        stream_id = d.pop("streamId")

        geo_json_layer = cls(
            stream_id=stream_id,
        )

        geo_json_layer.additional_properties = d
        return geo_json_layer

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
