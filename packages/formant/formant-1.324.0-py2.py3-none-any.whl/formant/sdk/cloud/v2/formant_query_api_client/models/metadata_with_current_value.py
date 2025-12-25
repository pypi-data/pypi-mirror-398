import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union

import attr
from dateutil.parser import isoparse

from ..models.metadata_with_current_value_type import \
    MetadataWithCurrentValueType
from ..types import UNSET, Unset

if TYPE_CHECKING:
  from ..models.metadata_with_current_value_current_value import \
      MetadataWithCurrentValueCurrentValue
  from ..models.metadata_with_current_value_tags import \
      MetadataWithCurrentValueTags




T = TypeVar("T", bound="MetadataWithCurrentValue")

@attr.s(auto_attribs=True)
class MetadataWithCurrentValue:
    """
    Attributes:
        organization_id (str):
        device_id (str):
        name (str):
        type (MetadataWithCurrentValueType):
        current_value_time (Union[Unset, datetime.datetime]):
        current_value (Union[Unset, MetadataWithCurrentValueCurrentValue]):
        id (Union[Unset, str]):
        created_at (Union[Unset, datetime.datetime]):
        updated_at (Union[Unset, datetime.datetime]):
        tags (Union[Unset, MetadataWithCurrentValueTags]):
        flushed_to_clickhouse (Union[Unset, bool]):
    """

    organization_id: str
    device_id: str
    name: str
    type: MetadataWithCurrentValueType
    current_value_time: Union[Unset, datetime.datetime] = UNSET
    current_value: Union[Unset, 'MetadataWithCurrentValueCurrentValue'] = UNSET
    id: Union[Unset, str] = UNSET
    created_at: Union[Unset, datetime.datetime] = UNSET
    updated_at: Union[Unset, datetime.datetime] = UNSET
    tags: Union[Unset, 'MetadataWithCurrentValueTags'] = UNSET
    flushed_to_clickhouse: Union[Unset, bool] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        organization_id = self.organization_id
        device_id = self.device_id
        name = self.name
        type = self.type.value

        current_value_time: Union[Unset, str] = UNSET
        if not isinstance(self.current_value_time, Unset):
            current_value_time = self.current_value_time.isoformat()

        current_value: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.current_value, Unset):
            current_value = self.current_value.to_dict()

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

        flushed_to_clickhouse = self.flushed_to_clickhouse

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "organizationId": organization_id,
            "deviceId": device_id,
            "name": name,
            "type": type,
        })
        if current_value_time is not UNSET:
            field_dict["currentValueTime"] = current_value_time
        if current_value is not UNSET:
            field_dict["currentValue"] = current_value
        if id is not UNSET:
            field_dict["id"] = id
        if created_at is not UNSET:
            field_dict["createdAt"] = created_at
        if updated_at is not UNSET:
            field_dict["updatedAt"] = updated_at
        if tags is not UNSET:
            field_dict["tags"] = tags
        if flushed_to_clickhouse is not UNSET:
            field_dict["flushedToClickhouse"] = flushed_to_clickhouse

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.metadata_with_current_value_current_value import \
            MetadataWithCurrentValueCurrentValue
        from ..models.metadata_with_current_value_tags import \
            MetadataWithCurrentValueTags
        d = src_dict.copy()
        organization_id = d.pop("organizationId")

        device_id = d.pop("deviceId")

        name = d.pop("name")

        type = MetadataWithCurrentValueType(d.pop("type"))




        _current_value_time = d.pop("currentValueTime", UNSET)
        current_value_time: Union[Unset, datetime.datetime]
        if isinstance(_current_value_time,  Unset):
            current_value_time = UNSET
        else:
            current_value_time = isoparse(_current_value_time)




        _current_value = d.pop("currentValue", UNSET)
        current_value: Union[Unset, MetadataWithCurrentValueCurrentValue]
        if isinstance(_current_value,  Unset):
            current_value = UNSET
        else:
            current_value = MetadataWithCurrentValueCurrentValue.from_dict(_current_value)




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
        tags: Union[Unset, MetadataWithCurrentValueTags]
        if isinstance(_tags,  Unset):
            tags = UNSET
        else:
            tags = MetadataWithCurrentValueTags.from_dict(_tags)




        flushed_to_clickhouse = d.pop("flushedToClickhouse", UNSET)

        metadata_with_current_value = cls(
            organization_id=organization_id,
            device_id=device_id,
            name=name,
            type=type,
            current_value_time=current_value_time,
            current_value=current_value,
            id=id,
            created_at=created_at,
            updated_at=updated_at,
            tags=tags,
            flushed_to_clickhouse=flushed_to_clickhouse,
        )

        metadata_with_current_value.additional_properties = d
        return metadata_with_current_value

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
