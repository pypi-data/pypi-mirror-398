import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar

import attr
from dateutil.parser import isoparse

if TYPE_CHECKING:
  from ..models.device_stream_streams import DeviceStreamStreams
  from ..models.device_stream_tags import DeviceStreamTags




T = TypeVar("T", bound="DeviceStream")

@attr.s(auto_attribs=True)
class DeviceStream:
    """
    Attributes:
        id (str):
        organization_id (str):
        name (str):
        tags (DeviceStreamTags):
        last_seen (datetime.datetime):
        online (bool):
        streams (DeviceStreamStreams):
    """

    id: str
    organization_id: str
    name: str
    tags: 'DeviceStreamTags'
    last_seen: datetime.datetime
    online: bool
    streams: 'DeviceStreamStreams'
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        id = self.id
        organization_id = self.organization_id
        name = self.name
        tags = self.tags.to_dict()

        last_seen = self.last_seen.isoformat()

        online = self.online
        streams = self.streams.to_dict()


        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "id": id,
            "organizationId": organization_id,
            "name": name,
            "tags": tags,
            "lastSeen": last_seen,
            "online": online,
            "streams": streams,
        })

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.device_stream_streams import DeviceStreamStreams
        from ..models.device_stream_tags import DeviceStreamTags
        d = src_dict.copy()
        id = d.pop("id")

        organization_id = d.pop("organizationId")

        name = d.pop("name")

        tags = DeviceStreamTags.from_dict(d.pop("tags"))




        last_seen = isoparse(d.pop("lastSeen"))




        online = d.pop("online")

        streams = DeviceStreamStreams.from_dict(d.pop("streams"))




        device_stream = cls(
            id=id,
            organization_id=organization_id,
            name=name,
            tags=tags,
            last_seen=last_seen,
            online=online,
            streams=streams,
        )

        device_stream.additional_properties = d
        return device_stream

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
