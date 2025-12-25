import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union

import attr
from dateutil.parser import isoparse

from ..models.command_response_stream_type import CommandResponseStreamType
from ..types import UNSET, Unset

if TYPE_CHECKING:
  from ..models.command_response_tags import CommandResponseTags




T = TypeVar("T", bound="CommandResponse")

@attr.s(auto_attribs=True)
class CommandResponse:
    """
    Attributes:
        time (datetime.datetime):
        message (str):
        success (bool):
        reply_to_command_request_id (str):
        device_id (Union[Unset, str]):
        stream_name (Union[Unset, str]):
        stream_type (Union[Unset, CommandResponseStreamType]):
        tags (Union[Unset, CommandResponseTags]):
        canceled_at (Union[Unset, datetime.datetime]):
        created_at (Union[Unset, datetime.datetime]):
        updated_at (Union[Unset, datetime.datetime]):
    """

    time: datetime.datetime
    message: str
    success: bool
    reply_to_command_request_id: str
    device_id: Union[Unset, str] = UNSET
    stream_name: Union[Unset, str] = UNSET
    stream_type: Union[Unset, CommandResponseStreamType] = UNSET
    tags: Union[Unset, 'CommandResponseTags'] = UNSET
    canceled_at: Union[Unset, datetime.datetime] = UNSET
    created_at: Union[Unset, datetime.datetime] = UNSET
    updated_at: Union[Unset, datetime.datetime] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        time = self.time.isoformat()

        message = self.message
        success = self.success
        reply_to_command_request_id = self.reply_to_command_request_id
        device_id = self.device_id
        stream_name = self.stream_name
        stream_type: Union[Unset, str] = UNSET
        if not isinstance(self.stream_type, Unset):
            stream_type = self.stream_type.value

        tags: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.tags, Unset):
            tags = self.tags.to_dict()

        canceled_at: Union[Unset, str] = UNSET
        if not isinstance(self.canceled_at, Unset):
            canceled_at = self.canceled_at.isoformat()

        created_at: Union[Unset, str] = UNSET
        if not isinstance(self.created_at, Unset):
            created_at = self.created_at.isoformat()

        updated_at: Union[Unset, str] = UNSET
        if not isinstance(self.updated_at, Unset):
            updated_at = self.updated_at.isoformat()


        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "time": time,
            "message": message,
            "success": success,
            "replyToCommandRequestId": reply_to_command_request_id,
        })
        if device_id is not UNSET:
            field_dict["deviceId"] = device_id
        if stream_name is not UNSET:
            field_dict["streamName"] = stream_name
        if stream_type is not UNSET:
            field_dict["streamType"] = stream_type
        if tags is not UNSET:
            field_dict["tags"] = tags
        if canceled_at is not UNSET:
            field_dict["canceledAt"] = canceled_at
        if created_at is not UNSET:
            field_dict["createdAt"] = created_at
        if updated_at is not UNSET:
            field_dict["updatedAt"] = updated_at

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.command_response_tags import CommandResponseTags
        d = src_dict.copy()
        time = isoparse(d.pop("time"))




        message = d.pop("message")

        success = d.pop("success")

        reply_to_command_request_id = d.pop("replyToCommandRequestId")

        device_id = d.pop("deviceId", UNSET)

        stream_name = d.pop("streamName", UNSET)

        _stream_type = d.pop("streamType", UNSET)
        stream_type: Union[Unset, CommandResponseStreamType]
        if isinstance(_stream_type,  Unset):
            stream_type = UNSET
        else:
            stream_type = CommandResponseStreamType(_stream_type)




        _tags = d.pop("tags", UNSET)
        tags: Union[Unset, CommandResponseTags]
        if isinstance(_tags,  Unset):
            tags = UNSET
        else:
            tags = CommandResponseTags.from_dict(_tags)




        _canceled_at = d.pop("canceledAt", UNSET)
        canceled_at: Union[Unset, datetime.datetime]
        if isinstance(_canceled_at,  Unset):
            canceled_at = UNSET
        else:
            canceled_at = isoparse(_canceled_at)




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




        command_response = cls(
            time=time,
            message=message,
            success=success,
            reply_to_command_request_id=reply_to_command_request_id,
            device_id=device_id,
            stream_name=stream_name,
            stream_type=stream_type,
            tags=tags,
            canceled_at=canceled_at,
            created_at=created_at,
            updated_at=updated_at,
        )

        command_response.additional_properties = d
        return command_response

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
