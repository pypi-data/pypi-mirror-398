import datetime
from typing import Any, Dict, List, Type, TypeVar, Union

import attr
from dateutil.parser import isoparse

from ..models.partial_stream_stream_type import PartialStreamStreamType
from ..types import UNSET, Unset

T = TypeVar("T", bound="PartialStream")

@attr.s(auto_attribs=True)
class PartialStream:
    """
    Attributes:
        organization_id (Union[Unset, str]):
        stream_name (Union[Unset, str]):
        stream_type (Union[Unset, PartialStreamStreamType]):
        description (Union[Unset, None, str]):
        alias (Union[Unset, None, str]):
        is_telemetry_filter (Union[Unset, bool]):
        is_event_filter (Union[Unset, bool]):
        active (Union[Unset, bool]):
        is_overview_column (Union[Unset, bool]):
        is_overview_row (Union[Unset, bool]):
        enabled (Union[Unset, bool]):
        id (Union[Unset, str]):
        created_at (Union[Unset, datetime.datetime]):
        updated_at (Union[Unset, datetime.datetime]):
    """

    organization_id: Union[Unset, str] = UNSET
    stream_name: Union[Unset, str] = UNSET
    stream_type: Union[Unset, PartialStreamStreamType] = UNSET
    description: Union[Unset, None, str] = UNSET
    alias: Union[Unset, None, str] = UNSET
    is_telemetry_filter: Union[Unset, bool] = UNSET
    is_event_filter: Union[Unset, bool] = UNSET
    active: Union[Unset, bool] = UNSET
    is_overview_column: Union[Unset, bool] = UNSET
    is_overview_row: Union[Unset, bool] = UNSET
    enabled: Union[Unset, bool] = UNSET
    id: Union[Unset, str] = UNSET
    created_at: Union[Unset, datetime.datetime] = UNSET
    updated_at: Union[Unset, datetime.datetime] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        organization_id = self.organization_id
        stream_name = self.stream_name
        stream_type: Union[Unset, str] = UNSET
        if not isinstance(self.stream_type, Unset):
            stream_type = self.stream_type.value

        description = self.description
        alias = self.alias
        is_telemetry_filter = self.is_telemetry_filter
        is_event_filter = self.is_event_filter
        active = self.active
        is_overview_column = self.is_overview_column
        is_overview_row = self.is_overview_row
        enabled = self.enabled
        id = self.id
        created_at: Union[Unset, str] = UNSET
        if not isinstance(self.created_at, Unset):
            created_at = self.created_at.isoformat()

        updated_at: Union[Unset, str] = UNSET
        if not isinstance(self.updated_at, Unset):
            updated_at = self.updated_at.isoformat()


        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
        })
        if organization_id is not UNSET:
            field_dict["organizationId"] = organization_id
        if stream_name is not UNSET:
            field_dict["streamName"] = stream_name
        if stream_type is not UNSET:
            field_dict["streamType"] = stream_type
        if description is not UNSET:
            field_dict["description"] = description
        if alias is not UNSET:
            field_dict["alias"] = alias
        if is_telemetry_filter is not UNSET:
            field_dict["isTelemetryFilter"] = is_telemetry_filter
        if is_event_filter is not UNSET:
            field_dict["isEventFilter"] = is_event_filter
        if active is not UNSET:
            field_dict["active"] = active
        if is_overview_column is not UNSET:
            field_dict["isOverviewColumn"] = is_overview_column
        if is_overview_row is not UNSET:
            field_dict["isOverviewRow"] = is_overview_row
        if enabled is not UNSET:
            field_dict["enabled"] = enabled
        if id is not UNSET:
            field_dict["id"] = id
        if created_at is not UNSET:
            field_dict["createdAt"] = created_at
        if updated_at is not UNSET:
            field_dict["updatedAt"] = updated_at

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        organization_id = d.pop("organizationId", UNSET)

        stream_name = d.pop("streamName", UNSET)

        _stream_type = d.pop("streamType", UNSET)
        stream_type: Union[Unset, PartialStreamStreamType]
        if isinstance(_stream_type,  Unset):
            stream_type = UNSET
        else:
            stream_type = PartialStreamStreamType(_stream_type)




        description = d.pop("description", UNSET)

        alias = d.pop("alias", UNSET)

        is_telemetry_filter = d.pop("isTelemetryFilter", UNSET)

        is_event_filter = d.pop("isEventFilter", UNSET)

        active = d.pop("active", UNSET)

        is_overview_column = d.pop("isOverviewColumn", UNSET)

        is_overview_row = d.pop("isOverviewRow", UNSET)

        enabled = d.pop("enabled", UNSET)

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




        partial_stream = cls(
            organization_id=organization_id,
            stream_name=stream_name,
            stream_type=stream_type,
            description=description,
            alias=alias,
            is_telemetry_filter=is_telemetry_filter,
            is_event_filter=is_event_filter,
            active=active,
            is_overview_column=is_overview_column,
            is_overview_row=is_overview_row,
            enabled=enabled,
            id=id,
            created_at=created_at,
            updated_at=updated_at,
        )

        partial_stream.additional_properties = d
        return partial_stream

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
