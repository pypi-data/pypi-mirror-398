import datetime
from typing import Any, Dict, List, Type, TypeVar, Union

import attr
from dateutil.parser import isoparse

from ..models.keyring_auth_type import KeyringAuthType
from ..types import UNSET, Unset

T = TypeVar("T", bound="Keyring")

@attr.s(auto_attribs=True)
class Keyring:
    """
    Attributes:
        organization_id (str):
        integration_id (str):
        auth_type (KeyringAuthType):
        access_token (str):
        user_id (Union[Unset, None, str]):
        refresh_token (Union[Unset, None, str]):
        expires_at (Union[Unset, None, datetime.datetime]):
        id (Union[Unset, str]):
        created_at (Union[Unset, datetime.datetime]):
        updated_at (Union[Unset, datetime.datetime]):
    """

    organization_id: str
    integration_id: str
    auth_type: KeyringAuthType
    access_token: str
    user_id: Union[Unset, None, str] = UNSET
    refresh_token: Union[Unset, None, str] = UNSET
    expires_at: Union[Unset, None, datetime.datetime] = UNSET
    id: Union[Unset, str] = UNSET
    created_at: Union[Unset, datetime.datetime] = UNSET
    updated_at: Union[Unset, datetime.datetime] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        organization_id = self.organization_id
        integration_id = self.integration_id
        auth_type = self.auth_type.value

        access_token = self.access_token
        user_id = self.user_id
        refresh_token = self.refresh_token
        expires_at: Union[Unset, None, str] = UNSET
        if not isinstance(self.expires_at, Unset):
            expires_at = self.expires_at.isoformat() if self.expires_at else None

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
            "organizationId": organization_id,
            "integrationId": integration_id,
            "authType": auth_type,
            "accessToken": access_token,
        })
        if user_id is not UNSET:
            field_dict["userId"] = user_id
        if refresh_token is not UNSET:
            field_dict["refreshToken"] = refresh_token
        if expires_at is not UNSET:
            field_dict["expiresAt"] = expires_at
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
        organization_id = d.pop("organizationId")

        integration_id = d.pop("integrationId")

        auth_type = KeyringAuthType(d.pop("authType"))




        access_token = d.pop("accessToken")

        user_id = d.pop("userId", UNSET)

        refresh_token = d.pop("refreshToken", UNSET)

        _expires_at = d.pop("expiresAt", UNSET)
        expires_at: Union[Unset, None, datetime.datetime]
        if _expires_at is None:
            expires_at = None
        elif isinstance(_expires_at,  Unset):
            expires_at = UNSET
        else:
            expires_at = isoparse(_expires_at)




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




        keyring = cls(
            organization_id=organization_id,
            integration_id=integration_id,
            auth_type=auth_type,
            access_token=access_token,
            user_id=user_id,
            refresh_token=refresh_token,
            expires_at=expires_at,
            id=id,
            created_at=created_at,
            updated_at=updated_at,
        )

        keyring.additional_properties = d
        return keyring

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
