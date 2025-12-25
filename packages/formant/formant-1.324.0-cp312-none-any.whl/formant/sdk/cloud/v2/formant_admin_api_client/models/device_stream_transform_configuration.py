from typing import Any, Dict, List, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

T = TypeVar("T", bound="DeviceStreamTransformConfiguration")

@attr.s(auto_attribs=True)
class DeviceStreamTransformConfiguration:
    """
    Attributes:
        video_encoding_enabled (Union[Unset, bool]):
    """

    video_encoding_enabled: Union[Unset, bool] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        video_encoding_enabled = self.video_encoding_enabled

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
        })
        if video_encoding_enabled is not UNSET:
            field_dict["videoEncodingEnabled"] = video_encoding_enabled

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        video_encoding_enabled = d.pop("videoEncodingEnabled", UNSET)

        device_stream_transform_configuration = cls(
            video_encoding_enabled=video_encoding_enabled,
        )

        device_stream_transform_configuration.additional_properties = d
        return device_stream_transform_configuration

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
