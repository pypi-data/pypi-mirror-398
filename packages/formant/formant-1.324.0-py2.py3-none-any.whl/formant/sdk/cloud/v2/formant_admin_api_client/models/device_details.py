import datetime
from typing import (TYPE_CHECKING, Any, Dict, List, Optional, Type, TypeVar,
                    Union)

import attr
from dateutil.parser import isoparse

from ..models.device_details_type import DeviceDetailsType
from ..types import UNSET, Unset

if TYPE_CHECKING:
  from ..models.device_details_tags import DeviceDetailsTags




T = TypeVar("T", bound="DeviceDetails")

@attr.s(auto_attribs=True)
class DeviceDetails:
    """
    Attributes:
        created_at (datetime.datetime):
        updated_at (datetime.datetime):
        id (str):
        name (str):
        type (DeviceDetailsType):
        tags (DeviceDetailsTags):
        enabled (bool):
        public_key (str):
        description (Optional[str]):
        online (Optional[bool]):
        last_seen (Optional[datetime.datetime]):
        agent_version (Optional[str]):
        disabled_at (Optional[datetime.datetime]):
        external_id (Union[Unset, None, str]):
    """

    created_at: datetime.datetime
    updated_at: datetime.datetime
    id: str
    name: str
    type: DeviceDetailsType
    tags: 'DeviceDetailsTags'
    enabled: bool
    public_key: str
    description: Optional[str]
    online: Optional[bool]
    last_seen: Optional[datetime.datetime]
    agent_version: Optional[str]
    disabled_at: Optional[datetime.datetime]
    external_id: Union[Unset, None, str] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        created_at = self.created_at.isoformat()

        updated_at = self.updated_at.isoformat()

        id = self.id
        name = self.name
        type = self.type.value

        tags = self.tags.to_dict()

        enabled = self.enabled
        public_key = self.public_key
        description = self.description
        online = self.online
        last_seen = self.last_seen.isoformat() if self.last_seen else None

        agent_version = self.agent_version
        disabled_at = self.disabled_at.isoformat() if self.disabled_at else None

        external_id = self.external_id

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "createdAt": created_at,
            "updatedAt": updated_at,
            "id": id,
            "name": name,
            "type": type,
            "tags": tags,
            "enabled": enabled,
            "publicKey": public_key,
            "description": description,
            "online": online,
            "lastSeen": last_seen,
            "agentVersion": agent_version,
            "disabledAt": disabled_at,
        })
        if external_id is not UNSET:
            field_dict["externalId"] = external_id

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.device_details_tags import DeviceDetailsTags
        d = src_dict.copy()
        created_at = isoparse(d.pop("createdAt"))




        updated_at = isoparse(d.pop("updatedAt"))




        id = d.pop("id")

        name = d.pop("name")

        type = DeviceDetailsType(d.pop("type"))




        tags = DeviceDetailsTags.from_dict(d.pop("tags"))




        enabled = d.pop("enabled")

        public_key = d.pop("publicKey")

        description = d.pop("description")

        online = d.pop("online")

        _last_seen = d.pop("lastSeen")
        last_seen: Optional[datetime.datetime]
        if _last_seen is None:
            last_seen = None
        else:
            last_seen = isoparse(_last_seen)




        agent_version = d.pop("agentVersion")

        _disabled_at = d.pop("disabledAt")
        disabled_at: Optional[datetime.datetime]
        if _disabled_at is None:
            disabled_at = None
        else:
            disabled_at = isoparse(_disabled_at)




        external_id = d.pop("externalId", UNSET)

        device_details = cls(
            created_at=created_at,
            updated_at=updated_at,
            id=id,
            name=name,
            type=type,
            tags=tags,
            enabled=enabled,
            public_key=public_key,
            description=description,
            online=online,
            last_seen=last_seen,
            agent_version=agent_version,
            disabled_at=disabled_at,
            external_id=external_id,
        )

        device_details.additional_properties = d
        return device_details

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
