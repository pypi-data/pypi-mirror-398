from typing import Any, Dict, List, Type, TypeVar, Union

import attr

from ..models.video_mime_type import VideoMimeType
from ..types import UNSET, Unset

T = TypeVar("T", bound="Video")

@attr.s(auto_attribs=True)
class Video:
    """
    Attributes:
        url (str):
        duration (int):
        mime_type (VideoMimeType):
        size (Union[Unset, int]):
    """

    url: str
    duration: int
    mime_type: VideoMimeType
    size: Union[Unset, int] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        url = self.url
        duration = self.duration
        mime_type = self.mime_type.value

        size = self.size

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "url": url,
            "duration": duration,
            "mimeType": mime_type,
        })
        if size is not UNSET:
            field_dict["size"] = size

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        url = d.pop("url")

        duration = d.pop("duration")

        mime_type = VideoMimeType(d.pop("mimeType"))




        size = d.pop("size", UNSET)

        video = cls(
            url=url,
            duration=duration,
            mime_type=mime_type,
            size=size,
        )

        video.additional_properties = d
        return video

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
