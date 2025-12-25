import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union

import attr
from dateutil.parser import isoparse

from ..types import UNSET, Unset

if TYPE_CHECKING:
  from ..models.create_service_account_request_tags import \
      CreateServiceAccountRequestTags
  from ..models.user_scope import UserScope




T = TypeVar("T", bound="CreateServiceAccountRequest")

@attr.s(auto_attribs=True)
class CreateServiceAccountRequest:
    """
    Attributes:
        name (str): Name of this service account.
        role_id (str): ID of the role for this service account.
        account_id (Union[Unset, str]): ID of the account to which this service account belongs.
        scope (Union[Unset, None, UserScope]):
        description (Union[Unset, None, str]):
        id (Union[Unset, str]):
        created_at (Union[Unset, datetime.datetime]):
        updated_at (Union[Unset, datetime.datetime]):
        tags (Union[Unset, CreateServiceAccountRequestTags]):
    """

    name: str
    role_id: str
    account_id: Union[Unset, str] = UNSET
    scope: Union[Unset, None, 'UserScope'] = UNSET
    description: Union[Unset, None, str] = UNSET
    id: Union[Unset, str] = UNSET
    created_at: Union[Unset, datetime.datetime] = UNSET
    updated_at: Union[Unset, datetime.datetime] = UNSET
    tags: Union[Unset, 'CreateServiceAccountRequestTags'] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        name = self.name
        role_id = self.role_id
        account_id = self.account_id
        scope: Union[Unset, None, Dict[str, Any]] = UNSET
        if not isinstance(self.scope, Unset):
            scope = self.scope.to_dict() if self.scope else None

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
            "roleId": role_id,
        })
        if account_id is not UNSET:
            field_dict["accountId"] = account_id
        if scope is not UNSET:
            field_dict["scope"] = scope
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
        from ..models.create_service_account_request_tags import \
            CreateServiceAccountRequestTags
        from ..models.user_scope import UserScope
        d = src_dict.copy()
        name = d.pop("name")

        role_id = d.pop("roleId")

        account_id = d.pop("accountId", UNSET)

        _scope = d.pop("scope", UNSET)
        scope: Union[Unset, None, UserScope]
        if _scope is None:
            scope = None
        elif isinstance(_scope,  Unset):
            scope = UNSET
        else:
            scope = UserScope.from_dict(_scope)




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
        tags: Union[Unset, CreateServiceAccountRequestTags]
        if isinstance(_tags,  Unset):
            tags = UNSET
        else:
            tags = CreateServiceAccountRequestTags.from_dict(_tags)




        create_service_account_request = cls(
            name=name,
            role_id=role_id,
            account_id=account_id,
            scope=scope,
            description=description,
            id=id,
            created_at=created_at,
            updated_at=updated_at,
            tags=tags,
        )

        create_service_account_request.additional_properties = d
        return create_service_account_request

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
