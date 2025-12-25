import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union

import attr
from dateutil.parser import isoparse

from ..models.metadata_type import MetadataType
from ..types import UNSET, Unset

if TYPE_CHECKING:
  from ..models.metadata_tags import MetadataTags




T = TypeVar("T", bound="Metadata")

@attr.s(auto_attribs=True)
class Metadata:
    """
    Attributes:
        organization_id (str):
        device_id (str):
        name (str):
        type (MetadataType):
        tags (Union[Unset, MetadataTags]):
        flushed_to_clickhouse (Union[Unset, bool]):
        updated_at (Union[Unset, datetime.datetime]):
        id (Union[Unset, str]):
        created_at (Union[Unset, datetime.datetime]):
    """

    organization_id: str
    device_id: str
    name: str
    type: MetadataType
    tags: Union[Unset, 'MetadataTags'] = UNSET
    flushed_to_clickhouse: Union[Unset, bool] = UNSET
    updated_at: Union[Unset, datetime.datetime] = UNSET
    id: Union[Unset, str] = UNSET
    created_at: Union[Unset, datetime.datetime] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        organization_id = self.organization_id
        device_id = self.device_id
        name = self.name
        type = self.type.value

        tags: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.tags, Unset):
            tags = self.tags.to_dict()

        flushed_to_clickhouse = self.flushed_to_clickhouse
        updated_at: Union[Unset, str] = UNSET
        if not isinstance(self.updated_at, Unset):
            updated_at = self.updated_at.isoformat()

        id = self.id
        created_at: Union[Unset, str] = UNSET
        if not isinstance(self.created_at, Unset):
            created_at = self.created_at.isoformat()


        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "organizationId": organization_id,
            "deviceId": device_id,
            "name": name,
            "type": type,
        })
        if tags is not UNSET:
            field_dict["tags"] = tags
        if flushed_to_clickhouse is not UNSET:
            field_dict["flushedToClickhouse"] = flushed_to_clickhouse
        if updated_at is not UNSET:
            field_dict["updatedAt"] = updated_at
        if id is not UNSET:
            field_dict["id"] = id
        if created_at is not UNSET:
            field_dict["createdAt"] = created_at

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.metadata_tags import MetadataTags
        d = src_dict.copy()
        organization_id = d.pop("organizationId")

        device_id = d.pop("deviceId")

        name = d.pop("name")

        type = MetadataType(d.pop("type"))




        _tags = d.pop("tags", UNSET)
        tags: Union[Unset, MetadataTags]
        if isinstance(_tags,  Unset):
            tags = UNSET
        else:
            tags = MetadataTags.from_dict(_tags)




        flushed_to_clickhouse = d.pop("flushedToClickhouse", UNSET)

        _updated_at = d.pop("updatedAt", UNSET)
        updated_at: Union[Unset, datetime.datetime]
        if isinstance(_updated_at,  Unset):
            updated_at = UNSET
        else:
            updated_at = isoparse(_updated_at)




        id = d.pop("id", UNSET)

        _created_at = d.pop("createdAt", UNSET)
        created_at: Union[Unset, datetime.datetime]
        if isinstance(_created_at,  Unset):
            created_at = UNSET
        else:
            created_at = isoparse(_created_at)




        metadata = cls(
            organization_id=organization_id,
            device_id=device_id,
            name=name,
            type=type,
            tags=tags,
            flushed_to_clickhouse=flushed_to_clickhouse,
            updated_at=updated_at,
            id=id,
            created_at=created_at,
        )

        metadata.additional_properties = d
        return metadata

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
