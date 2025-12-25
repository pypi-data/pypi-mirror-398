import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union

import attr
from dateutil.parser import isoparse

from ..types import UNSET, Unset

if TYPE_CHECKING:
  from ..models.cloud_file_tags import CloudFileTags




T = TypeVar("T", bound="CloudFile")

@attr.s(auto_attribs=True)
class CloudFile:
    """
    Attributes:
        name (str):
        organization_id (str):
        user_id (str):
        file_id (str):
        file_size (int):
        id (Union[Unset, str]):
        created_at (Union[Unset, datetime.datetime]):
        updated_at (Union[Unset, datetime.datetime]):
        tags (Union[Unset, CloudFileTags]):
    """

    name: str
    organization_id: str
    user_id: str
    file_id: str
    file_size: int
    id: Union[Unset, str] = UNSET
    created_at: Union[Unset, datetime.datetime] = UNSET
    updated_at: Union[Unset, datetime.datetime] = UNSET
    tags: Union[Unset, 'CloudFileTags'] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        name = self.name
        organization_id = self.organization_id
        user_id = self.user_id
        file_id = self.file_id
        file_size = self.file_size
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


        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "name": name,
            "organizationId": organization_id,
            "userId": user_id,
            "fileId": file_id,
            "fileSize": file_size,
        })
        if id is not UNSET:
            field_dict["id"] = id
        if created_at is not UNSET:
            field_dict["createdAt"] = created_at
        if updated_at is not UNSET:
            field_dict["updatedAt"] = updated_at
        if tags is not UNSET:
            field_dict["tags"] = tags

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.cloud_file_tags import CloudFileTags
        d = src_dict.copy()
        name = d.pop("name")

        organization_id = d.pop("organizationId")

        user_id = d.pop("userId")

        file_id = d.pop("fileId")

        file_size = d.pop("fileSize")

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
        tags: Union[Unset, CloudFileTags]
        if isinstance(_tags,  Unset):
            tags = UNSET
        else:
            tags = CloudFileTags.from_dict(_tags)




        cloud_file = cls(
            name=name,
            organization_id=organization_id,
            user_id=user_id,
            file_id=file_id,
            file_size=file_size,
            id=id,
            created_at=created_at,
            updated_at=updated_at,
            tags=tags,
        )

        cloud_file.additional_properties = d
        return cloud_file

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
