import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union

import attr
from dateutil.parser import isoparse

from ..models.integration_auth_type import IntegrationAuthType
from ..types import UNSET, Unset

if TYPE_CHECKING:
  from ..models.o_auth_configuration import OAuthConfiguration




T = TypeVar("T", bound="Integration")

@attr.s(auto_attribs=True)
class Integration:
    """
    Attributes:
        name (str):
        auth_type (IntegrationAuthType):
        auth_config (Union[Unset, None, OAuthConfiguration]):
        id (Union[Unset, str]):
        created_at (Union[Unset, datetime.datetime]):
        updated_at (Union[Unset, datetime.datetime]):
        deleted_at (Union[Unset, None, datetime.datetime]):
    """

    name: str
    auth_type: IntegrationAuthType
    auth_config: Union[Unset, None, 'OAuthConfiguration'] = UNSET
    id: Union[Unset, str] = UNSET
    created_at: Union[Unset, datetime.datetime] = UNSET
    updated_at: Union[Unset, datetime.datetime] = UNSET
    deleted_at: Union[Unset, None, datetime.datetime] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        name = self.name
        auth_type = self.auth_type.value

        auth_config: Union[Unset, None, Dict[str, Any]] = UNSET
        if not isinstance(self.auth_config, Unset):
            auth_config = self.auth_config.to_dict() if self.auth_config else None

        id = self.id
        created_at: Union[Unset, str] = UNSET
        if not isinstance(self.created_at, Unset):
            created_at = self.created_at.isoformat()

        updated_at: Union[Unset, str] = UNSET
        if not isinstance(self.updated_at, Unset):
            updated_at = self.updated_at.isoformat()

        deleted_at: Union[Unset, None, str] = UNSET
        if not isinstance(self.deleted_at, Unset):
            deleted_at = self.deleted_at.isoformat() if self.deleted_at else None


        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "name": name,
            "authType": auth_type,
        })
        if auth_config is not UNSET:
            field_dict["authConfig"] = auth_config
        if id is not UNSET:
            field_dict["id"] = id
        if created_at is not UNSET:
            field_dict["createdAt"] = created_at
        if updated_at is not UNSET:
            field_dict["updatedAt"] = updated_at
        if deleted_at is not UNSET:
            field_dict["deletedAt"] = deleted_at

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.o_auth_configuration import OAuthConfiguration
        d = src_dict.copy()
        name = d.pop("name")

        auth_type = IntegrationAuthType(d.pop("authType"))




        _auth_config = d.pop("authConfig", UNSET)
        auth_config: Union[Unset, None, OAuthConfiguration]
        if _auth_config is None:
            auth_config = None
        elif isinstance(_auth_config,  Unset):
            auth_config = UNSET
        else:
            auth_config = OAuthConfiguration.from_dict(_auth_config)




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




        _deleted_at = d.pop("deletedAt", UNSET)
        deleted_at: Union[Unset, None, datetime.datetime]
        if _deleted_at is None:
            deleted_at = None
        elif isinstance(_deleted_at,  Unset):
            deleted_at = UNSET
        else:
            deleted_at = isoparse(_deleted_at)




        integration = cls(
            name=name,
            auth_type=auth_type,
            auth_config=auth_config,
            id=id,
            created_at=created_at,
            updated_at=updated_at,
            deleted_at=deleted_at,
        )

        integration.additional_properties = d
        return integration

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
