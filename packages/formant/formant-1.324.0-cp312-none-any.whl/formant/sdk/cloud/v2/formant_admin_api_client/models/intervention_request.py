import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union, cast

import attr
from dateutil.parser import isoparse

from ..models.intervention_request_intervention_type import \
    InterventionRequestInterventionType
from ..models.intervention_request_severity import InterventionRequestSeverity
from ..models.intervention_request_stream_type import \
    InterventionRequestStreamType
from ..models.intervention_request_type import InterventionRequestType
from ..types import UNSET, Unset

if TYPE_CHECKING:
  from ..models.intervention_request_metadata import \
      InterventionRequestMetadata
  from ..models.intervention_request_tags import InterventionRequestTags
  from ..models.labeling_request_data import LabelingRequestData
  from ..models.notification_muted import NotificationMuted
  from ..models.physical_request_data import PhysicalRequestData
  from ..models.selection_request_data import SelectionRequestData
  from ..models.teleop_request_data import TeleopRequestData




T = TypeVar("T", bound="InterventionRequest")

@attr.s(auto_attribs=True)
class InterventionRequest:
    """
    Attributes:
        data (Union['LabelingRequestData', 'PhysicalRequestData', 'SelectionRequestData', 'TeleopRequestData']):
        time (datetime.datetime): Start time of the data range relevant to this event.
        type (Union[Unset, InterventionRequestType]): Enter `intervention-request`.
        intervention_type (Union[Unset, InterventionRequestInterventionType]): `selection` prompts user to select an
            option from a dropdown menu. `labeling` prompts user to draw a box around and object and give it a label.
        responses (Union[Unset, List[Any]]):
        agent_id (Union[Unset, str]): ID of the device which prompts this intervention request.
        severity (Union[Unset, InterventionRequestSeverity]): Severity of this event (`info`, `warning`, `error`, or
            `critical`).
        id (Union[Unset, str]):
        created_at (Union[Unset, datetime.datetime]):
        updated_at (Union[Unset, datetime.datetime]):
        tags (Union[Unset, InterventionRequestTags]):
        organization_id (Union[Unset, str]): ID of the organization in which to create this new event.
        external_id (Union[Unset, None, str]): External ID of this event.
        user_id (Union[Unset, None, str]): User ID associated with this event.
        end_time (Union[Unset, None, datetime.datetime]): End time of the data range relevant to this event.
        parent_id (Union[Unset, None, str]): If this custom event is related to another event, you can add the ID of
            that parent event here.
        metadata (Union[Unset, InterventionRequestMetadata]): User-customizable metadata associated with this event in
            key-value pair format.
        message (Union[Unset, str]): Message of this event. Must match the `message` field in the Formant UI when
            configuring a custom event.
        viewed (Union[Unset, bool]):
        device_id (Union[Unset, None, str]): ID of the device relevant to this event.
        stream_name (Union[Unset, None, str]):
        stream_type (Union[Unset, None, InterventionRequestStreamType]):
        event_trigger_id (Union[Unset, None, str]):
        notification_enabled (Union[Unset, bool]): Set this to `true` to enable notifications for this event.
        notification_muted (Union[Unset, None, NotificationMuted]):
        deleted_at (Union[Unset, None, datetime.datetime]):
    """

    data: Union['LabelingRequestData', 'PhysicalRequestData', 'SelectionRequestData', 'TeleopRequestData']
    time: datetime.datetime
    type: Union[Unset, InterventionRequestType] = UNSET
    intervention_type: Union[Unset, InterventionRequestInterventionType] = UNSET
    responses: Union[Unset, List[Any]] = UNSET
    agent_id: Union[Unset, str] = UNSET
    severity: Union[Unset, InterventionRequestSeverity] = UNSET
    id: Union[Unset, str] = UNSET
    created_at: Union[Unset, datetime.datetime] = UNSET
    updated_at: Union[Unset, datetime.datetime] = UNSET
    tags: Union[Unset, 'InterventionRequestTags'] = UNSET
    organization_id: Union[Unset, str] = UNSET
    external_id: Union[Unset, None, str] = UNSET
    user_id: Union[Unset, None, str] = UNSET
    end_time: Union[Unset, None, datetime.datetime] = UNSET
    parent_id: Union[Unset, None, str] = UNSET
    metadata: Union[Unset, 'InterventionRequestMetadata'] = UNSET
    message: Union[Unset, str] = UNSET
    viewed: Union[Unset, bool] = UNSET
    device_id: Union[Unset, None, str] = UNSET
    stream_name: Union[Unset, None, str] = UNSET
    stream_type: Union[Unset, None, InterventionRequestStreamType] = UNSET
    event_trigger_id: Union[Unset, None, str] = UNSET
    notification_enabled: Union[Unset, bool] = UNSET
    notification_muted: Union[Unset, None, 'NotificationMuted'] = UNSET
    deleted_at: Union[Unset, None, datetime.datetime] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        from ..models.labeling_request_data import LabelingRequestData
        from ..models.selection_request_data import SelectionRequestData
        from ..models.teleop_request_data import TeleopRequestData
        data: Dict[str, Any]

        if isinstance(self.data, SelectionRequestData):
            data = self.data.to_dict()

        elif isinstance(self.data, LabelingRequestData):
            data = self.data.to_dict()

        elif isinstance(self.data, TeleopRequestData):
            data = self.data.to_dict()

        else:
            data = self.data.to_dict()



        time = self.time.isoformat()

        type: Union[Unset, str] = UNSET
        if not isinstance(self.type, Unset):
            type = self.type.value

        intervention_type: Union[Unset, str] = UNSET
        if not isinstance(self.intervention_type, Unset):
            intervention_type = self.intervention_type.value

        responses: Union[Unset, List[Any]] = UNSET
        if not isinstance(self.responses, Unset):
            responses = self.responses




        agent_id = self.agent_id
        severity: Union[Unset, str] = UNSET
        if not isinstance(self.severity, Unset):
            severity = self.severity.value

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
            "data": data,
            "time": time,
        })
        if type is not UNSET:
            field_dict["type"] = type
        if intervention_type is not UNSET:
            field_dict["interventionType"] = intervention_type
        if responses is not UNSET:
            field_dict["responses"] = responses
        if agent_id is not UNSET:
            field_dict["agentId"] = agent_id
        if severity is not UNSET:
            field_dict["severity"] = severity
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
        from ..models.intervention_request_metadata import \
            InterventionRequestMetadata
        from ..models.intervention_request_tags import InterventionRequestTags
        from ..models.labeling_request_data import LabelingRequestData
        from ..models.notification_muted import NotificationMuted
        from ..models.physical_request_data import PhysicalRequestData
        from ..models.selection_request_data import SelectionRequestData
        from ..models.teleop_request_data import TeleopRequestData
        d = src_dict.copy()
        def _parse_data(data: object) -> Union['LabelingRequestData', 'PhysicalRequestData', 'SelectionRequestData', 'TeleopRequestData']:
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                data_type_0 = SelectionRequestData.from_dict(data)



                return data_type_0
            except: # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                data_type_1 = LabelingRequestData.from_dict(data)



                return data_type_1
            except: # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                data_type_2 = TeleopRequestData.from_dict(data)



                return data_type_2
            except: # noqa: E722
                pass
            if not isinstance(data, dict):
                raise TypeError()
            data_type_3 = PhysicalRequestData.from_dict(data)



            return data_type_3

        data = _parse_data(d.pop("data"))


        time = isoparse(d.pop("time"))




        _type = d.pop("type", UNSET)
        type: Union[Unset, InterventionRequestType]
        if isinstance(_type,  Unset):
            type = UNSET
        else:
            type = InterventionRequestType(_type)




        _intervention_type = d.pop("interventionType", UNSET)
        intervention_type: Union[Unset, InterventionRequestInterventionType]
        if isinstance(_intervention_type,  Unset):
            intervention_type = UNSET
        else:
            intervention_type = InterventionRequestInterventionType(_intervention_type)




        responses = cast(List[Any], d.pop("responses", UNSET))


        agent_id = d.pop("agentId", UNSET)

        _severity = d.pop("severity", UNSET)
        severity: Union[Unset, InterventionRequestSeverity]
        if isinstance(_severity,  Unset):
            severity = UNSET
        else:
            severity = InterventionRequestSeverity(_severity)




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
        tags: Union[Unset, InterventionRequestTags]
        if isinstance(_tags,  Unset):
            tags = UNSET
        else:
            tags = InterventionRequestTags.from_dict(_tags)




        organization_id = d.pop("organizationId", UNSET)

        external_id = d.pop("externalId", UNSET)

        user_id = d.pop("userId", UNSET)

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
        metadata: Union[Unset, InterventionRequestMetadata]
        if isinstance(_metadata,  Unset):
            metadata = UNSET
        else:
            metadata = InterventionRequestMetadata.from_dict(_metadata)




        message = d.pop("message", UNSET)

        viewed = d.pop("viewed", UNSET)

        device_id = d.pop("deviceId", UNSET)

        stream_name = d.pop("streamName", UNSET)

        _stream_type = d.pop("streamType", UNSET)
        stream_type: Union[Unset, None, InterventionRequestStreamType]
        if _stream_type is None:
            stream_type = None
        elif isinstance(_stream_type,  Unset):
            stream_type = UNSET
        else:
            stream_type = InterventionRequestStreamType(_stream_type)




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




        intervention_request = cls(
            data=data,
            time=time,
            type=type,
            intervention_type=intervention_type,
            responses=responses,
            agent_id=agent_id,
            severity=severity,
            id=id,
            created_at=created_at,
            updated_at=updated_at,
            tags=tags,
            organization_id=organization_id,
            external_id=external_id,
            user_id=user_id,
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

        intervention_request.additional_properties = d
        return intervention_request

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
