import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union

import attr
from dateutil.parser import isoparse

from ..models.partial_annotation_stream_type import PartialAnnotationStreamType
from ..models.partial_annotation_type import PartialAnnotationType
from ..types import UNSET, Unset

if TYPE_CHECKING:
  from ..models.focused_datapoint import FocusedDatapoint
  from ..models.notification_muted import NotificationMuted
  from ..models.partial_annotation_metadata import PartialAnnotationMetadata
  from ..models.partial_annotation_tags import PartialAnnotationTags
  from ..models.tag_sets import TagSets




T = TypeVar("T", bound="PartialAnnotation")

@attr.s(auto_attribs=True)
class PartialAnnotation:
    """
    Attributes:
        type (Union[Unset, PartialAnnotationType]):
        edited_at (Union[Unset, None, datetime.datetime]): Internal use only, ignore.
        user_id (Union[Unset, None, str]): User associated with this annotation.
        annotation_template_id (Union[Unset, None, str]): If you want to create this annotation from an existing
            annotation template, enter its ID here.
        tagged_users (Union[Unset, TagSets]): A map of tag keys to an array of values
        published_to (Union[Unset, Any]):
        note (Union[Unset, None, str]): Description of this annotation.
        focused_data_points (Union[Unset, None, List['FocusedDatapoint']]):
        id (Union[Unset, str]):
        created_at (Union[Unset, datetime.datetime]):
        updated_at (Union[Unset, datetime.datetime]):
        tags (Union[Unset, PartialAnnotationTags]):
        organization_id (Union[Unset, str]): ID of the organization in which to create this new event.
        external_id (Union[Unset, None, str]): External ID of this event.
        time (Union[Unset, datetime.datetime]): Start time of the data range relevant to this event.
        end_time (Union[Unset, None, datetime.datetime]): End time of the data range relevant to this event.
        parent_id (Union[Unset, None, str]): If this custom event is related to another event, you can add the ID of
            that parent event here.
        metadata (Union[Unset, PartialAnnotationMetadata]): User-customizable metadata associated with this event in
            key-value pair format.
        message (Union[Unset, str]): Message of this event. Must match the `message` field in the Formant UI when
            configuring a custom event.
        viewed (Union[Unset, bool]):
        device_id (Union[Unset, None, str]): ID of the device relevant to this event.
        stream_name (Union[Unset, None, str]):
        stream_type (Union[Unset, None, PartialAnnotationStreamType]):
        event_trigger_id (Union[Unset, None, str]):
        notification_enabled (Union[Unset, bool]): Set this to `true` to enable notifications for this event.
        notification_muted (Union[Unset, None, NotificationMuted]):
        deleted_at (Union[Unset, None, datetime.datetime]):
    """

    type: Union[Unset, PartialAnnotationType] = UNSET
    edited_at: Union[Unset, None, datetime.datetime] = UNSET
    user_id: Union[Unset, None, str] = UNSET
    annotation_template_id: Union[Unset, None, str] = UNSET
    tagged_users: Union[Unset, 'TagSets'] = UNSET
    published_to: Union[Unset, Any] = UNSET
    note: Union[Unset, None, str] = UNSET
    focused_data_points: Union[Unset, None, List['FocusedDatapoint']] = UNSET
    id: Union[Unset, str] = UNSET
    created_at: Union[Unset, datetime.datetime] = UNSET
    updated_at: Union[Unset, datetime.datetime] = UNSET
    tags: Union[Unset, 'PartialAnnotationTags'] = UNSET
    organization_id: Union[Unset, str] = UNSET
    external_id: Union[Unset, None, str] = UNSET
    time: Union[Unset, datetime.datetime] = UNSET
    end_time: Union[Unset, None, datetime.datetime] = UNSET
    parent_id: Union[Unset, None, str] = UNSET
    metadata: Union[Unset, 'PartialAnnotationMetadata'] = UNSET
    message: Union[Unset, str] = UNSET
    viewed: Union[Unset, bool] = UNSET
    device_id: Union[Unset, None, str] = UNSET
    stream_name: Union[Unset, None, str] = UNSET
    stream_type: Union[Unset, None, PartialAnnotationStreamType] = UNSET
    event_trigger_id: Union[Unset, None, str] = UNSET
    notification_enabled: Union[Unset, bool] = UNSET
    notification_muted: Union[Unset, None, 'NotificationMuted'] = UNSET
    deleted_at: Union[Unset, None, datetime.datetime] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        type: Union[Unset, str] = UNSET
        if not isinstance(self.type, Unset):
            type = self.type.value

        edited_at: Union[Unset, None, str] = UNSET
        if not isinstance(self.edited_at, Unset):
            edited_at = self.edited_at.isoformat() if self.edited_at else None

        user_id = self.user_id
        annotation_template_id = self.annotation_template_id
        tagged_users: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.tagged_users, Unset):
            tagged_users = self.tagged_users.to_dict()

        published_to = self.published_to
        note = self.note
        focused_data_points: Union[Unset, None, List[Dict[str, Any]]] = UNSET
        if not isinstance(self.focused_data_points, Unset):
            if self.focused_data_points is None:
                focused_data_points = None
            else:
                focused_data_points = []
                for focused_data_points_item_data in self.focused_data_points:
                    focused_data_points_item = focused_data_points_item_data.to_dict()

                    focused_data_points.append(focused_data_points_item)




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

        organization_id = self.organization_id
        external_id = self.external_id
        time: Union[Unset, str] = UNSET
        if not isinstance(self.time, Unset):
            time = self.time.isoformat()

        end_time: Union[Unset, None, str] = UNSET
        if not isinstance(self.end_time, Unset):
            end_time = self.end_time.isoformat() if self.end_time else None

        parent_id = self.parent_id
        metadata: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.metadata, Unset):
            metadata = self.metadata.to_dict()

        message = self.message
        viewed = self.viewed
        device_id = self.device_id
        stream_name = self.stream_name
        stream_type: Union[Unset, None, str] = UNSET
        if not isinstance(self.stream_type, Unset):
            stream_type = self.stream_type.value if self.stream_type else None

        event_trigger_id = self.event_trigger_id
        notification_enabled = self.notification_enabled
        notification_muted: Union[Unset, None, Dict[str, Any]] = UNSET
        if not isinstance(self.notification_muted, Unset):
            notification_muted = self.notification_muted.to_dict() if self.notification_muted else None

        deleted_at: Union[Unset, None, str] = UNSET
        if not isinstance(self.deleted_at, Unset):
            deleted_at = self.deleted_at.isoformat() if self.deleted_at else None


        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
        })
        if type is not UNSET:
            field_dict["type"] = type
        if edited_at is not UNSET:
            field_dict["editedAt"] = edited_at
        if user_id is not UNSET:
            field_dict["userId"] = user_id
        if annotation_template_id is not UNSET:
            field_dict["annotationTemplateId"] = annotation_template_id
        if tagged_users is not UNSET:
            field_dict["taggedUsers"] = tagged_users
        if published_to is not UNSET:
            field_dict["publishedTo"] = published_to
        if note is not UNSET:
            field_dict["note"] = note
        if focused_data_points is not UNSET:
            field_dict["focusedDataPoints"] = focused_data_points
        if id is not UNSET:
            field_dict["id"] = id
        if created_at is not UNSET:
            field_dict["createdAt"] = created_at
        if updated_at is not UNSET:
            field_dict["updatedAt"] = updated_at
        if tags is not UNSET:
            field_dict["tags"] = tags
        if organization_id is not UNSET:
            field_dict["organizationId"] = organization_id
        if external_id is not UNSET:
            field_dict["externalId"] = external_id
        if time is not UNSET:
            field_dict["time"] = time
        if end_time is not UNSET:
            field_dict["endTime"] = end_time
        if parent_id is not UNSET:
            field_dict["parentId"] = parent_id
        if metadata is not UNSET:
            field_dict["metadata"] = metadata
        if message is not UNSET:
            field_dict["message"] = message
        if viewed is not UNSET:
            field_dict["viewed"] = viewed
        if device_id is not UNSET:
            field_dict["deviceId"] = device_id
        if stream_name is not UNSET:
            field_dict["streamName"] = stream_name
        if stream_type is not UNSET:
            field_dict["streamType"] = stream_type
        if event_trigger_id is not UNSET:
            field_dict["eventTriggerId"] = event_trigger_id
        if notification_enabled is not UNSET:
            field_dict["notificationEnabled"] = notification_enabled
        if notification_muted is not UNSET:
            field_dict["notificationMuted"] = notification_muted
        if deleted_at is not UNSET:
            field_dict["deletedAt"] = deleted_at

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.focused_datapoint import FocusedDatapoint
        from ..models.notification_muted import NotificationMuted
        from ..models.partial_annotation_metadata import \
            PartialAnnotationMetadata
        from ..models.partial_annotation_tags import PartialAnnotationTags
        from ..models.tag_sets import TagSets
        d = src_dict.copy()
        _type = d.pop("type", UNSET)
        type: Union[Unset, PartialAnnotationType]
        if isinstance(_type,  Unset):
            type = UNSET
        else:
            type = PartialAnnotationType(_type)




        _edited_at = d.pop("editedAt", UNSET)
        edited_at: Union[Unset, None, datetime.datetime]
        if _edited_at is None:
            edited_at = None
        elif isinstance(_edited_at,  Unset):
            edited_at = UNSET
        else:
            edited_at = isoparse(_edited_at)




        user_id = d.pop("userId", UNSET)

        annotation_template_id = d.pop("annotationTemplateId", UNSET)

        _tagged_users = d.pop("taggedUsers", UNSET)
        tagged_users: Union[Unset, TagSets]
        if isinstance(_tagged_users,  Unset):
            tagged_users = UNSET
        else:
            tagged_users = TagSets.from_dict(_tagged_users)




        published_to = d.pop("publishedTo", UNSET)

        note = d.pop("note", UNSET)

        focused_data_points = []
        _focused_data_points = d.pop("focusedDataPoints", UNSET)
        for focused_data_points_item_data in (_focused_data_points or []):
            focused_data_points_item = FocusedDatapoint.from_dict(focused_data_points_item_data)



            focused_data_points.append(focused_data_points_item)


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
        tags: Union[Unset, PartialAnnotationTags]
        if isinstance(_tags,  Unset):
            tags = UNSET
        else:
            tags = PartialAnnotationTags.from_dict(_tags)




        organization_id = d.pop("organizationId", UNSET)

        external_id = d.pop("externalId", UNSET)

        _time = d.pop("time", UNSET)
        time: Union[Unset, datetime.datetime]
        if isinstance(_time,  Unset):
            time = UNSET
        else:
            time = isoparse(_time)




        _end_time = d.pop("endTime", UNSET)
        end_time: Union[Unset, None, datetime.datetime]
        if _end_time is None:
            end_time = None
        elif isinstance(_end_time,  Unset):
            end_time = UNSET
        else:
            end_time = isoparse(_end_time)




        parent_id = d.pop("parentId", UNSET)

        _metadata = d.pop("metadata", UNSET)
        metadata: Union[Unset, PartialAnnotationMetadata]
        if isinstance(_metadata,  Unset):
            metadata = UNSET
        else:
            metadata = PartialAnnotationMetadata.from_dict(_metadata)




        message = d.pop("message", UNSET)

        viewed = d.pop("viewed", UNSET)

        device_id = d.pop("deviceId", UNSET)

        stream_name = d.pop("streamName", UNSET)

        _stream_type = d.pop("streamType", UNSET)
        stream_type: Union[Unset, None, PartialAnnotationStreamType]
        if _stream_type is None:
            stream_type = None
        elif isinstance(_stream_type,  Unset):
            stream_type = UNSET
        else:
            stream_type = PartialAnnotationStreamType(_stream_type)




        event_trigger_id = d.pop("eventTriggerId", UNSET)

        notification_enabled = d.pop("notificationEnabled", UNSET)

        _notification_muted = d.pop("notificationMuted", UNSET)
        notification_muted: Union[Unset, None, NotificationMuted]
        if _notification_muted is None:
            notification_muted = None
        elif isinstance(_notification_muted,  Unset):
            notification_muted = UNSET
        else:
            notification_muted = NotificationMuted.from_dict(_notification_muted)




        _deleted_at = d.pop("deletedAt", UNSET)
        deleted_at: Union[Unset, None, datetime.datetime]
        if _deleted_at is None:
            deleted_at = None
        elif isinstance(_deleted_at,  Unset):
            deleted_at = UNSET
        else:
            deleted_at = isoparse(_deleted_at)




        partial_annotation = cls(
            type=type,
            edited_at=edited_at,
            user_id=user_id,
            annotation_template_id=annotation_template_id,
            tagged_users=tagged_users,
            published_to=published_to,
            note=note,
            focused_data_points=focused_data_points,
            id=id,
            created_at=created_at,
            updated_at=updated_at,
            tags=tags,
            organization_id=organization_id,
            external_id=external_id,
            time=time,
            end_time=end_time,
            parent_id=parent_id,
            metadata=metadata,
            message=message,
            viewed=viewed,
            device_id=device_id,
            stream_name=stream_name,
            stream_type=stream_type,
            event_trigger_id=event_trigger_id,
            notification_enabled=notification_enabled,
            notification_muted=notification_muted,
            deleted_at=deleted_at,
        )

        partial_annotation.additional_properties = d
        return partial_annotation

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
