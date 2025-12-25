import datetime
from typing import Any, Dict, List, Type, TypeVar, Union

import attr
from dateutil.parser import isoparse

from ..types import UNSET, Unset

T = TypeVar("T", bound="KeyringLoginResponse")

@attr.s(auto_attribs=True)
class KeyringLoginResponse:
    """
    Attributes:
        access_token (Union[Unset, None, str]):
        expires_at (Union[Unset, None, datetime.datetime]):
        user_action_url (Union[Unset, None, str]):
    """

    access_token: Union[Unset, None, str] = UNSET
    expires_at: Union[Unset, None, datetime.datetime] = UNSET
    user_action_url: Union[Unset, None, str] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        access_token = self.access_token
        expires_at: Union[Unset, None, str] = UNSET
        if not isinstance(self.expires_at, Unset):
            expires_at = self.expires_at.isoformat() if self.expires_at else None

        user_action_url = self.user_action_url

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
        })
        if access_token is not UNSET:
            field_dict["accessToken"] = access_token
        if expires_at is not UNSET:
            field_dict["expiresAt"] = expires_at
        if user_action_url is not UNSET:
            field_dict["userActionUrl"] = user_action_url

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        access_token = d.pop("accessToken", UNSET)

        _expires_at = d.pop("expiresAt", UNSET)
        expires_at: Union[Unset, None, datetime.datetime]
        if _expires_at is None:
            expires_at = None
        elif isinstance(_expires_at,  Unset):
            expires_at = UNSET
        else:
            expires_at = isoparse(_expires_at)




        user_action_url = d.pop("userActionUrl", UNSET)

        keyring_login_response = cls(
            access_token=access_token,
            expires_at=expires_at,
            user_action_url=user_action_url,
        )

        keyring_login_response.additional_properties = d
        return keyring_login_response

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
