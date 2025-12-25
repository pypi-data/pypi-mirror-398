import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union

import attr
from dateutil.parser import isoparse

from ..models.task_summary_stream_type import TaskSummaryStreamType
from ..models.task_summary_type import TaskSummaryType
from ..types import UNSET, Unset

if TYPE_CHECKING:
  from ..models.notification_muted import NotificationMuted
  from ..models.task_summary_metadata import TaskSummaryMetadata
  from ..models.task_summary_report import TaskSummaryReport
  from ..models.task_summary_tags import TaskSummaryTags




T = TypeVar("T", bound="TaskSummary")

@attr.s(auto_attribs=True)
class TaskSummary:
    """
    Attributes:
        task_summary_format_id (str): ID of the task summary format which describes this task summary.
        report (TaskSummaryReport): Enter the data for this task summary in key-value pairs, as described by the task
            summary format.
        task_id (str): Enter a unique identifier to identify this task summary.
        generated_at (datetime.datetime): Enter a start time for when this event occurred. This differs from
            `createdAt`, which is automatically populated when the task summary is created.
        time (datetime.datetime): Start time of the data range relevant to this event.
        type (Union[Unset, TaskSummaryType]): Enter `task-summary`.
        end_time (Union[Unset, None, datetime.datetime]): End time of the data range relevant to this event.
        id (Union[Unset, str]):
        created_at (Union[Unset, datetime.datetime]):
        updated_at (Union[Unset, datetime.datetime]):
        tags (Union[Unset, TaskSummaryTags]):
        organization_id (Union[Unset, str]): ID of the organization in which to create this new event.
        external_id (Union[Unset, None, str]): External ID of this event.
        user_id (Union[Unset, None, str]): User ID associated with this event.
        parent_id (Union[Unset, None, str]): If this custom event is related to another event, you can add the ID of
            that parent event here.
        metadata (Union[Unset, TaskSummaryMetadata]): User-customizable metadata associated with this event in key-value
            pair format.
        message (Union[Unset, str]): Message of this event. Must match the `message` field in the Formant UI when
            configuring a custom event.
        viewed (Union[Unset, bool]):
        device_id (Union[Unset, None, str]): ID of the device relevant to this event.
        stream_name (Union[Unset, None, str]):
        stream_type (Union[Unset, None, TaskSummaryStreamType]):
        event_trigger_id (Union[Unset, None, str]):
        notification_enabled (Union[Unset, bool]): Set this to `true` to enable notifications for this event.
        notification_muted (Union[Unset, None, NotificationMuted]):
        deleted_at (Union[Unset, None, datetime.datetime]):
    """

    task_summary_format_id: str
    report: 'TaskSummaryReport'
    task_id: str
    generated_at: datetime.datetime
    time: datetime.datetime
    type: Union[Unset, TaskSummaryType] = UNSET
    end_time: Union[Unset, None, datetime.datetime] = UNSET
    id: Union[Unset, str] = UNSET
    created_at: Union[Unset, datetime.datetime] = UNSET
    updated_at: Union[Unset, datetime.datetime] = UNSET
    tags: Union[Unset, 'TaskSummaryTags'] = UNSET
    organization_id: Union[Unset, str] = UNSET
    external_id: Union[Unset, None, str] = UNSET
    user_id: Union[Unset, None, str] = UNSET
    parent_id: Union[Unset, None, str] = UNSET
    metadata: Union[Unset, 'TaskSummaryMetadata'] = UNSET
    message: Union[Unset, str] = UNSET
    viewed: Union[Unset, bool] = UNSET
    device_id: Union[Unset, None, str] = UNSET
    stream_name: Union[Unset, None, str] = UNSET
    stream_type: Union[Unset, None, TaskSummaryStreamType] = UNSET
    event_trigger_id: Union[Unset, None, str] = UNSET
    notification_enabled: Union[Unset, bool] = UNSET
    notification_muted: Union[Unset, None, 'NotificationMuted'] = UNSET
    deleted_at: Union[Unset, None, datetime.datetime] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        task_summary_format_id = self.task_summary_format_id
        report = self.report.to_dict()

        task_id = self.task_id
        generated_at = self.generated_at.isoformat()

        time = self.time.isoformat()

        type: Union[Unset, str] = UNSET
        if not isinstance(self.type, Unset):
            type = self.type.value

        end_time: Union[Unset, None, str] = UNSET
        if not isinstance(self.end_time, Unset):
            end_time = self.end_time.isoformat() if self.end_time else None

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
        user_id = self.user_id
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
            "taskSummaryFormatId": task_summary_format_id,
            "report": report,
            "taskId": task_id,
            "generatedAt": generated_at,
            "time": time,
        })
        if type is not UNSET:
            field_dict["type"] = type
        if end_time is not UNSET:
            field_dict["endTime"] = end_time
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
        if user_id is not UNSET:
            field_dict["userId"] = user_id
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
        from ..models.notification_muted import NotificationMuted
        from ..models.task_summary_metadata import TaskSummaryMetadata
        from ..models.task_summary_report import TaskSummaryReport
        from ..models.task_summary_tags import TaskSummaryTags
        d = src_dict.copy()
        task_summary_format_id = d.pop("taskSummaryFormatId")

        report = TaskSummaryReport.from_dict(d.pop("report"))




        task_id = d.pop("taskId")

        generated_at = isoparse(d.pop("generatedAt"))




        time = isoparse(d.pop("time"))




        _type = d.pop("type", UNSET)
        type: Union[Unset, TaskSummaryType]
        if isinstance(_type,  Unset):
            type = UNSET
        else:
            type = TaskSummaryType(_type)




        _end_time = d.pop("endTime", UNSET)
        end_time: Union[Unset, None, datetime.datetime]
        if _end_time is None:
            end_time = None
        elif isinstance(_end_time,  Unset):
            end_time = UNSET
        else:
            end_time = isoparse(_end_time)




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
        tags: Union[Unset, TaskSummaryTags]
        if isinstance(_tags,  Unset):
            tags = UNSET
        else:
            tags = TaskSummaryTags.from_dict(_tags)




        organization_id = d.pop("organizationId", UNSET)

        external_id = d.pop("externalId", UNSET)

        user_id = d.pop("userId", UNSET)

        parent_id = d.pop("parentId", UNSET)

        _metadata = d.pop("metadata", UNSET)
        metadata: Union[Unset, TaskSummaryMetadata]
        if isinstance(_metadata,  Unset):
            metadata = UNSET
        else:
            metadata = TaskSummaryMetadata.from_dict(_metadata)




        message = d.pop("message", UNSET)

        viewed = d.pop("viewed", UNSET)

        device_id = d.pop("deviceId", UNSET)

        stream_name = d.pop("streamName", UNSET)

        _stream_type = d.pop("streamType", UNSET)
        stream_type: Union[Unset, None, TaskSummaryStreamType]
        if _stream_type is None:
            stream_type = None
        elif isinstance(_stream_type,  Unset):
            stream_type = UNSET
        else:
            stream_type = TaskSummaryStreamType(_stream_type)




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




        task_summary = cls(
            task_summary_format_id=task_summary_format_id,
            report=report,
            task_id=task_id,
            generated_at=generated_at,
            time=time,
            type=type,
            end_time=end_time,
            id=id,
            created_at=created_at,
            updated_at=updated_at,
            tags=tags,
            organization_id=organization_id,
            external_id=external_id,
            user_id=user_id,
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

        task_summary.additional_properties = d
        return task_summary

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
