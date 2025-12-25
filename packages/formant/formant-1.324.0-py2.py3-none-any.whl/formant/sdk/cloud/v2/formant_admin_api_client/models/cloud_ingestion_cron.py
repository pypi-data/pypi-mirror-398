import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union

import attr
from dateutil.parser import isoparse

from ..models.cloud_ingestion_cron_handler_type import \
    CloudIngestionCronHandlerType
from ..types import UNSET, Unset

if TYPE_CHECKING:
  from ..models.cloud_ingestion_cron_tags import CloudIngestionCronTags




T = TypeVar("T", bound="CloudIngestionCron")

@attr.s(auto_attribs=True)
class CloudIngestionCron:
    """
    Attributes:
        organization_id (str):
        handler_type (CloudIngestionCronHandlerType):
        handler_uri (str):
        application_name (str):
        run_period_seconds (int):
        enabled (Union[Unset, bool]):
        last_execution_id (Union[Unset, None, str]):
        id (Union[Unset, str]):
        created_at (Union[Unset, datetime.datetime]):
        updated_at (Union[Unset, datetime.datetime]):
        tags (Union[Unset, CloudIngestionCronTags]):
        deleted_at (Union[Unset, None, datetime.datetime]):
    """

    organization_id: str
    handler_type: CloudIngestionCronHandlerType
    handler_uri: str
    application_name: str
    run_period_seconds: int
    enabled: Union[Unset, bool] = UNSET
    last_execution_id: Union[Unset, None, str] = UNSET
    id: Union[Unset, str] = UNSET
    created_at: Union[Unset, datetime.datetime] = UNSET
    updated_at: Union[Unset, datetime.datetime] = UNSET
    tags: Union[Unset, 'CloudIngestionCronTags'] = UNSET
    deleted_at: Union[Unset, None, datetime.datetime] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        organization_id = self.organization_id
        handler_type = self.handler_type.value

        handler_uri = self.handler_uri
        application_name = self.application_name
        run_period_seconds = self.run_period_seconds
        enabled = self.enabled
        last_execution_id = self.last_execution_id
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

        deleted_at: Union[Unset, None, str] = UNSET
        if not isinstance(self.deleted_at, Unset):
            deleted_at = self.deleted_at.isoformat() if self.deleted_at else None


        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "organizationId": organization_id,
            "handlerType": handler_type,
            "handlerUri": handler_uri,
            "applicationName": application_name,
            "runPeriodSeconds": run_period_seconds,
        })
        if enabled is not UNSET:
            field_dict["enabled"] = enabled
        if last_execution_id is not UNSET:
            field_dict["lastExecutionId"] = last_execution_id
        if id is not UNSET:
            field_dict["id"] = id
        if created_at is not UNSET:
            field_dict["createdAt"] = created_at
        if updated_at is not UNSET:
            field_dict["updatedAt"] = updated_at
        if tags is not UNSET:
            field_dict["tags"] = tags
        if deleted_at is not UNSET:
            field_dict["deletedAt"] = deleted_at

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.cloud_ingestion_cron_tags import CloudIngestionCronTags
        d = src_dict.copy()
        organization_id = d.pop("organizationId")

        handler_type = CloudIngestionCronHandlerType(d.pop("handlerType"))




        handler_uri = d.pop("handlerUri")

        application_name = d.pop("applicationName")

        run_period_seconds = d.pop("runPeriodSeconds")

        enabled = d.pop("enabled", UNSET)

        last_execution_id = d.pop("lastExecutionId", UNSET)

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
        tags: Union[Unset, CloudIngestionCronTags]
        if isinstance(_tags,  Unset):
            tags = UNSET
        else:
            tags = CloudIngestionCronTags.from_dict(_tags)




        _deleted_at = d.pop("deletedAt", UNSET)
        deleted_at: Union[Unset, None, datetime.datetime]
        if _deleted_at is None:
            deleted_at = None
        elif isinstance(_deleted_at,  Unset):
            deleted_at = UNSET
        else:
            deleted_at = isoparse(_deleted_at)




        cloud_ingestion_cron = cls(
            organization_id=organization_id,
            handler_type=handler_type,
            handler_uri=handler_uri,
            application_name=application_name,
            run_period_seconds=run_period_seconds,
            enabled=enabled,
            last_execution_id=last_execution_id,
            id=id,
            created_at=created_at,
            updated_at=updated_at,
            tags=tags,
            deleted_at=deleted_at,
        )

        cloud_ingestion_cron.additional_properties = d
        return cloud_ingestion_cron

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
