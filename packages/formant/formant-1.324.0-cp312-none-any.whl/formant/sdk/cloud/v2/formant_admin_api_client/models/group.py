import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union

import attr
from dateutil.parser import isoparse

from ..types import UNSET, Unset

if TYPE_CHECKING:
  from ..models.group_tags import GroupTags




T = TypeVar("T", bound="Group")

@attr.s(auto_attribs=True)
class Group:
    """
    Attributes:
        name (str):
        tag_key (Any):
        tag_value (Any):
        organization_id (Union[Unset, str]):
        active (Union[Unset, bool]):
        enabled (Union[Unset, bool]):
        color (Union[Unset, None, str]):
        parent (Union[Unset, None, str]):
        description (Union[Unset, None, str]):
        id (Union[Unset, str]):
        created_at (Union[Unset, datetime.datetime]):
        updated_at (Union[Unset, datetime.datetime]):
        tags (Union[Unset, GroupTags]):
    """

    name: str
    tag_key: Any
    tag_value: Any
    organization_id: Union[Unset, str] = UNSET
    active: Union[Unset, bool] = UNSET
    enabled: Union[Unset, bool] = UNSET
    color: Union[Unset, None, str] = UNSET
    parent: Union[Unset, None, str] = UNSET
    description: Union[Unset, None, str] = UNSET
    id: Union[Unset, str] = UNSET
    created_at: Union[Unset, datetime.datetime] = UNSET
    updated_at: Union[Unset, datetime.datetime] = UNSET
    tags: Union[Unset, 'GroupTags'] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        name = self.name
        tag_key = self.tag_key
        tag_value = self.tag_value
        organization_id = self.organization_id
        active = self.active
        enabled = self.enabled
        color = self.color
        parent = self.parent
        description = self.description
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
            "tagKey": tag_key,
            "tagValue": tag_value,
        })
        if organization_id is not UNSET:
            field_dict["organizationId"] = organization_id
        if active is not UNSET:
            field_dict["active"] = active
        if enabled is not UNSET:
            field_dict["enabled"] = enabled
        if color is not UNSET:
            field_dict["color"] = color
        if parent is not UNSET:
            field_dict["parent"] = parent
        if description is not UNSET:
            field_dict["description"] = description
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
        from ..models.group_tags import GroupTags
        d = src_dict.copy()
        name = d.pop("name")

        tag_key = d.pop("tagKey")

        tag_value = d.pop("tagValue")

        organization_id = d.pop("organizationId", UNSET)

        active = d.pop("active", UNSET)

        enabled = d.pop("enabled", UNSET)

        color = d.pop("color", UNSET)

        parent = d.pop("parent", UNSET)

        description = d.pop("description", UNSET)

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
        tags: Union[Unset, GroupTags]
        if isinstance(_tags,  Unset):
            tags = UNSET
        else:
            tags = GroupTags.from_dict(_tags)




        group = cls(
            name=name,
            tag_key=tag_key,
            tag_value=tag_value,
            organization_id=organization_id,
            active=active,
            enabled=enabled,
            color=color,
            parent=parent,
            description=description,
            id=id,
            created_at=created_at,
            updated_at=updated_at,
            tags=tags,
        )

        group.additional_properties = d
        return group

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
