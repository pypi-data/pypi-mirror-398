import datetime
from typing import Any, Dict, List, Optional, Type, TypeVar, Union

import attr
from dateutil.parser import isoparse

from ..models.schedule_type import ScheduleType
from ..types import UNSET, Unset

T = TypeVar("T", bound="Schedule")

@attr.s(auto_attribs=True)
class Schedule:
    """
    Attributes:
        name (str): Name of this schedule.
        description (str): User-friendly description of this command schedule.
        type (ScheduleType): Enter `command`.
        duration_ms (int): Enter `0` for this parameter.
        timezone (str): Timezone which corresponds to the timestamp provided in the `at` parameter, in `tz database`
            format.
        device_id (str): ID of the device to which to send this command.
        organization_id (Union[Unset, str]): ID of the organization to which you want to add this new schedule.
        at (Optional[datetime.datetime]): Timestamp at which this command should execute. Must be in the future. Format:
            `YYYY-MM-DDTHH:MM:SS`
        cron (Optional[str]): Frequency of this command schedule, as defined at https://crontab.guru
        display_timezone (Union[Unset, Any]):
        command_template_id (Optional[str]): You must create a command template before you can schedule this command.
        compose_operation_id (Union[Unset, None, str]): Runs theopolis task source.
        workflow_id (Union[Unset, None, str]):
        parameter_value (Optional[str]): Value of the command parameter to be sent with this scheduled command.
        status (Union[Unset, str]): Internal use only, ignore.
        id (Union[Unset, str]):
        created_at (Union[Unset, datetime.datetime]):
        updated_at (Union[Unset, datetime.datetime]):
    """

    name: str
    description: str
    type: ScheduleType
    duration_ms: int
    timezone: str
    device_id: str
    at: Optional[datetime.datetime]
    cron: Optional[str]
    command_template_id: Optional[str]
    parameter_value: Optional[str]
    organization_id: Union[Unset, str] = UNSET
    display_timezone: Union[Unset, Any] = UNSET
    compose_operation_id: Union[Unset, None, str] = UNSET
    workflow_id: Union[Unset, None, str] = UNSET
    status: Union[Unset, str] = UNSET
    id: Union[Unset, str] = UNSET
    created_at: Union[Unset, datetime.datetime] = UNSET
    updated_at: Union[Unset, datetime.datetime] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        name = self.name
        description = self.description
        type = self.type.value

        duration_ms = self.duration_ms
        timezone = self.timezone
        device_id = self.device_id
        organization_id = self.organization_id
        at = self.at.isoformat() if self.at else None

        cron = self.cron
        display_timezone = self.display_timezone
        command_template_id = self.command_template_id
        compose_operation_id = self.compose_operation_id
        workflow_id = self.workflow_id
        parameter_value = self.parameter_value
        status = self.status
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
            "name": name,
            "description": description,
            "type": type,
            "durationMs": duration_ms,
            "timezone": timezone,
            "deviceId": device_id,
            "at": at,
            "cron": cron,
            "commandTemplateId": command_template_id,
            "parameterValue": parameter_value,
        })
        if organization_id is not UNSET:
            field_dict["organizationId"] = organization_id
        if display_timezone is not UNSET:
            field_dict["displayTimezone"] = display_timezone
        if compose_operation_id is not UNSET:
            field_dict["composeOperationId"] = compose_operation_id
        if workflow_id is not UNSET:
            field_dict["workflowId"] = workflow_id
        if status is not UNSET:
            field_dict["status"] = status
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
        name = d.pop("name")

        description = d.pop("description")

        type = ScheduleType(d.pop("type"))




        duration_ms = d.pop("durationMs")

        timezone = d.pop("timezone")

        device_id = d.pop("deviceId")

        organization_id = d.pop("organizationId", UNSET)

        _at = d.pop("at")
        at: Optional[datetime.datetime]
        if _at is None:
            at = None
        else:
            at = isoparse(_at)




        cron = d.pop("cron")

        display_timezone = d.pop("displayTimezone", UNSET)

        command_template_id = d.pop("commandTemplateId")

        compose_operation_id = d.pop("composeOperationId", UNSET)

        workflow_id = d.pop("workflowId", UNSET)

        parameter_value = d.pop("parameterValue")

        status = d.pop("status", UNSET)

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




        schedule = cls(
            name=name,
            description=description,
            type=type,
            duration_ms=duration_ms,
            timezone=timezone,
            device_id=device_id,
            organization_id=organization_id,
            at=at,
            cron=cron,
            display_timezone=display_timezone,
            command_template_id=command_template_id,
            compose_operation_id=compose_operation_id,
            workflow_id=workflow_id,
            parameter_value=parameter_value,
            status=status,
            id=id,
            created_at=created_at,
            updated_at=updated_at,
        )

        schedule.additional_properties = d
        return schedule

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
