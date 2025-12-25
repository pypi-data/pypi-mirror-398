import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union

import attr
from dateutil.parser import isoparse

from ..types import UNSET, Unset

if TYPE_CHECKING:
  from ..models.capture_session_tags import CaptureSessionTags




T = TypeVar("T", bound="CaptureSession")

@attr.s(auto_attribs=True)
class CaptureSession:
    """
    Attributes:
        device_id (str): ID of the device with which you want to associate this capture session.
        stream_name (str): Name of the stream to which your video device will publish data.
        organization_id (Union[Unset, str]): ID of the organization to which you want to save this capture session.
        user_id (Union[Unset, str]):
        code (Union[Unset, str]):
        expiration (Union[Unset, None, datetime.datetime]): Date and time when the capture session link sent to your
            video device will expire.
        id (Union[Unset, str]):
        created_at (Union[Unset, datetime.datetime]):
        updated_at (Union[Unset, datetime.datetime]):
        tags (Union[Unset, CaptureSessionTags]):
    """

    device_id: str
    stream_name: str
    organization_id: Union[Unset, str] = UNSET
    user_id: Union[Unset, str] = UNSET
    code: Union[Unset, str] = UNSET
    expiration: Union[Unset, None, datetime.datetime] = UNSET
    id: Union[Unset, str] = UNSET
    created_at: Union[Unset, datetime.datetime] = UNSET
    updated_at: Union[Unset, datetime.datetime] = UNSET
    tags: Union[Unset, 'CaptureSessionTags'] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        device_id = self.device_id
        stream_name = self.stream_name
        organization_id = self.organization_id
        user_id = self.user_id
        code = self.code
        expiration: Union[Unset, None, str] = UNSET
        if not isinstance(self.expiration, Unset):
            expiration = self.expiration.isoformat() if self.expiration else None

        id = self.id
        created_at: Union[Unset, str] = UNSET
        if not isinstance(self.created_at, Unset):
            created_at = self.created_at.isoformat()

        updated_at: Union[Unset, str] = UNSET
        if not isinstance(self.updated_at, Unset):
            updated_at = self.updated_at.isoformat()

        tags: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.tags, Unset):
            tags = self.tags.to_dict()


        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "deviceId": device_id,
            "streamName": stream_name,
        })
        if organization_id is not UNSET:
            field_dict["organizationId"] = organization_id
        if user_id is not UNSET:
            field_dict["userId"] = user_id
        if code is not UNSET:
            field_dict["code"] = code
        if expiration is not UNSET:
            field_dict["expiration"] = expiration
        if id is not UNSET:
            field_dict["id"] = id
        if created_at is not UNSET:
            field_dict["createdAt"] = created_at
        if updated_at is not UNSET:
            field_dict["updatedAt"] = updated_at
        if tags is not UNSET:
            field_dict["tags"] = tags

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.capture_session_tags import CaptureSessionTags
        d = src_dict.copy()
        device_id = d.pop("deviceId")

        stream_name = d.pop("streamName")

        organization_id = d.pop("organizationId", UNSET)

        user_id = d.pop("userId", UNSET)

        code = d.pop("code", UNSET)

        _expiration = d.pop("expiration", UNSET)
        expiration: Union[Unset, None, datetime.datetime]
        if _expiration is None:
            expiration = None
        elif isinstance(_expiration,  Unset):
            expiration = UNSET
        else:
            expiration = isoparse(_expiration)




        id = d.pop("id", UNSET)

        _created_at = d.pop("createdAt", UNSET)
        created_at: Union[Unset, datetime.datetime]
        if isinstance(_created_at,  Unset):
            created_at = UNSET
        else:
            created_at = isoparse(_created_at)




        _updated_at = d.pop("updatedAt", UNSET)
        updated_at: Union[Unset, datetime.datetime]
        if isinstance(_updated_at,  Unset):
            updated_at = UNSET
        else:
            updated_at = isoparse(_updated_at)




        _tags = d.pop("tags", UNSET)
        tags: Union[Unset, CaptureSessionTags]
        if isinstance(_tags,  Unset):
            tags = UNSET
        else:
            tags = CaptureSessionTags.from_dict(_tags)




        capture_session = cls(
            device_id=device_id,
            stream_name=stream_name,
            organization_id=organization_id,
            user_id=user_id,
            code=code,
            expiration=expiration,
            id=id,
            created_at=created_at,
            updated_at=updated_at,
            tags=tags,
        )

        capture_session.additional_properties = d
        return capture_session

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
