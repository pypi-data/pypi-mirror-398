import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union

import attr
from dateutil.parser import isoparse

from ..types import UNSET, Unset

if TYPE_CHECKING:
  from ..models.team_tags import TeamTags
  from ..models.user_scope import UserScope




T = TypeVar("T", bound="Team")

@attr.s(auto_attribs=True)
class Team:
    """
    Attributes:
        name (str): Name of this team.
        role_id (str): ID of the role which will be assigned to all members of this team.
        organization_id (Union[Unset, str]): ID of the organization to which this team belongs.
        scope (Union[Unset, None, UserScope]):
        id (Union[Unset, str]):
        created_at (Union[Unset, datetime.datetime]):
        updated_at (Union[Unset, datetime.datetime]):
        tags (Union[Unset, TeamTags]):
        deleted_at (Union[Unset, None, datetime.datetime]):
    """

    name: str
    role_id: str
    organization_id: Union[Unset, str] = UNSET
    scope: Union[Unset, None, 'UserScope'] = UNSET
    id: Union[Unset, str] = UNSET
    created_at: Union[Unset, datetime.datetime] = UNSET
    updated_at: Union[Unset, datetime.datetime] = UNSET
    tags: Union[Unset, 'TeamTags'] = UNSET
    deleted_at: Union[Unset, None, datetime.datetime] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        name = self.name
        role_id = self.role_id
        organization_id = self.organization_id
        scope: Union[Unset, None, Dict[str, Any]] = UNSET
        if not isinstance(self.scope, Unset):
            scope = self.scope.to_dict() if self.scope else None

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
            "name": name,
            "roleId": role_id,
        })
        if organization_id is not UNSET:
            field_dict["organizationId"] = organization_id
        if scope is not UNSET:
            field_dict["scope"] = scope
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
        from ..models.team_tags import TeamTags
        from ..models.user_scope import UserScope
        d = src_dict.copy()
        name = d.pop("name")

        role_id = d.pop("roleId")

        organization_id = d.pop("organizationId", UNSET)

        _scope = d.pop("scope", UNSET)
        scope: Union[Unset, None, UserScope]
        if _scope is None:
            scope = None
        elif isinstance(_scope,  Unset):
            scope = UNSET
        else:
            scope = UserScope.from_dict(_scope)




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
        tags: Union[Unset, TeamTags]
        if isinstance(_tags,  Unset):
            tags = UNSET
        else:
            tags = TeamTags.from_dict(_tags)




        _deleted_at = d.pop("deletedAt", UNSET)
        deleted_at: Union[Unset, None, datetime.datetime]
        if _deleted_at is None:
            deleted_at = None
        elif isinstance(_deleted_at,  Unset):
            deleted_at = UNSET
        else:
            deleted_at = isoparse(_deleted_at)




        team = cls(
            name=name,
            role_id=role_id,
            organization_id=organization_id,
            scope=scope,
            id=id,
            created_at=created_at,
            updated_at=updated_at,
            tags=tags,
            deleted_at=deleted_at,
        )

        team.additional_properties = d
        return team

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
