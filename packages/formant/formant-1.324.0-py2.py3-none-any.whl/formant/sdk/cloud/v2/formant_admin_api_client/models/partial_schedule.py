import datetime
from typing import Any, Dict, List, Type, TypeVar, Union

import attr
from dateutil.parser import isoparse

from ..models.partial_schedule_type import PartialScheduleType
from ..types import UNSET, Unset

T = TypeVar("T", bound="PartialSchedule")

@attr.s(auto_attribs=True)
class PartialSchedule:
    """
    Attributes:
        organization_id (Union[Unset, str]): ID of the organization to which you want to add this new schedule.
        name (Union[Unset, str]): Name of this schedule.
        description (Union[Unset, str]): User-friendly description of this command schedule.
        type (Union[Unset, PartialScheduleType]): Enter `command`.
        at (Union[Unset, None, datetime.datetime]): Timestamp at which this command should execute. Must be in the
            future. Format: `YYYY-MM-DDTHH:MM:SS`
        cron (Union[Unset, None, str]): Frequency of this command schedule, as defined at https://crontab.guru
        duration_ms (Union[Unset, int]): Enter `0` for this parameter.
        timezone (Union[Unset, str]): Timezone which corresponds to the timestamp provided in the `at` parameter, in `tz
            database` format.
        display_timezone (Union[Unset, Any]):
        command_template_id (Union[Unset, None, str]): You must create a command template before you can schedule this
            command.
        compose_operation_id (Union[Unset, None, str]): Runs theopolis task source.
        workflow_id (Union[Unset, None, str]):
        parameter_value (Union[Unset, None, str]): Value of the command parameter to be sent with this scheduled
            command.
        device_id (Union[Unset, str]): ID of the device to which to send this command.
        status (Union[Unset, str]): Internal use only, ignore.
        id (Union[Unset, str]):
        created_at (Union[Unset, datetime.datetime]):
        updated_at (Union[Unset, datetime.datetime]):
    """

    organization_id: Union[Unset, str] = UNSET
    name: Union[Unset, str] = UNSET
    description: Union[Unset, str] = UNSET
    type: Union[Unset, PartialScheduleType] = UNSET
    at: Union[Unset, None, datetime.datetime] = UNSET
    cron: Union[Unset, None, str] = UNSET
    duration_ms: Union[Unset, int] = UNSET
    timezone: Union[Unset, str] = UNSET
    display_timezone: Union[Unset, Any] = UNSET
    command_template_id: Union[Unset, None, str] = UNSET
    compose_operation_id: Union[Unset, None, str] = UNSET
    workflow_id: Union[Unset, None, str] = UNSET
    parameter_value: Union[Unset, None, str] = UNSET
    device_id: Union[Unset, str] = UNSET
    status: Union[Unset, str] = UNSET
    id: Union[Unset, str] = UNSET
    created_at: Union[Unset, datetime.datetime] = UNSET
    updated_at: Union[Unset, datetime.datetime] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        organization_id = self.organization_id
        name = self.name
        description = self.description
        type: Union[Unset, str] = UNSET
        if not isinstance(self.type, Unset):
            type = self.type.value

        at: Union[Unset, None, str] = UNSET
        if not isinstance(self.at, Unset):
            at = self.at.isoformat() if self.at else None

        cron = self.cron
        duration_ms = self.duration_ms
        timezone = self.timezone
        display_timezone = self.display_timezone
        command_template_id = self.command_template_id
        compose_operation_id = self.compose_operation_id
        workflow_id = self.workflow_id
        parameter_value = self.parameter_value
        device_id = self.device_id
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
        })
        if organization_id is not UNSET:
            field_dict["organizationId"] = organization_id
        if name is not UNSET:
            field_dict["name"] = name
        if description is not UNSET:
            field_dict["description"] = description
        if type is not UNSET:
            field_dict["type"] = type
        if at is not UNSET:
            field_dict["at"] = at
        if cron is not UNSET:
            field_dict["cron"] = cron
        if duration_ms is not UNSET:
            field_dict["durationMs"] = duration_ms
        if timezone is not UNSET:
            field_dict["timezone"] = timezone
        if display_timezone is not UNSET:
            field_dict["displayTimezone"] = display_timezone
        if command_template_id is not UNSET:
            field_dict["commandTemplateId"] = command_template_id
        if compose_operation_id is not UNSET:
            field_dict["composeOperationId"] = compose_operation_id
        if workflow_id is not UNSET:
            field_dict["workflowId"] = workflow_id
        if parameter_value is not UNSET:
            field_dict["parameterValue"] = parameter_value
        if device_id is not UNSET:
            field_dict["deviceId"] = device_id
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
        organization_id = d.pop("organizationId", UNSET)

        name = d.pop("name", UNSET)

        description = d.pop("description", UNSET)

        _type = d.pop("type", UNSET)
        type: Union[Unset, PartialScheduleType]
        if isinstance(_type,  Unset):
            type = UNSET
        else:
            type = PartialScheduleType(_type)




        _at = d.pop("at", UNSET)
        at: Union[Unset, None, datetime.datetime]
        if _at is None:
            at = None
        elif isinstance(_at,  Unset):
            at = UNSET
        else:
            at = isoparse(_at)




        cron = d.pop("cron", UNSET)

        duration_ms = d.pop("durationMs", UNSET)

        timezone = d.pop("timezone", UNSET)

        display_timezone = d.pop("displayTimezone", UNSET)

        command_template_id = d.pop("commandTemplateId", UNSET)

        compose_operation_id = d.pop("composeOperationId", UNSET)

        workflow_id = d.pop("workflowId", UNSET)

        parameter_value = d.pop("parameterValue", UNSET)

        device_id = d.pop("deviceId", UNSET)

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




        partial_schedule = cls(
            organization_id=organization_id,
            name=name,
            description=description,
            type=type,
            at=at,
            cron=cron,
            duration_ms=duration_ms,
            timezone=timezone,
            display_timezone=display_timezone,
            command_template_id=command_template_id,
            compose_operation_id=compose_operation_id,
            workflow_id=workflow_id,
            parameter_value=parameter_value,
            device_id=device_id,
            status=status,
            id=id,
            created_at=created_at,
            updated_at=updated_at,
        )

        partial_schedule.additional_properties = d
        return partial_schedule

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
