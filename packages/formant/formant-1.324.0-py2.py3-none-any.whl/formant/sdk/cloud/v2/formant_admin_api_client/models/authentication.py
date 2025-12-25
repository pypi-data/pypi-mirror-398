from typing import Any, Dict, List, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

T = TypeVar("T", bound="Authentication")

@attr.s(auto_attribs=True)
class Authentication:
    """
    Attributes:
        access_token (str):
        organization_id (str):
        user_id (str):
        refresh_token (Union[Unset, str]):
        is_superuser (Union[Unset, bool]):
    """

    access_token: str
    organization_id: str
    user_id: str
    refresh_token: Union[Unset, str] = UNSET
    is_superuser: Union[Unset, bool] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        access_token = self.access_token
        organization_id = self.organization_id
        user_id = self.user_id
        refresh_token = self.refresh_token
        is_superuser = self.is_superuser

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "accessToken": access_token,
            "organizationId": organization_id,
            "userId": user_id,
        })
        if refresh_token is not UNSET:
            field_dict["refreshToken"] = refresh_token
        if is_superuser is not UNSET:
            field_dict["isSuperuser"] = is_superuser

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        access_token = d.pop("accessToken")

        organization_id = d.pop("organizationId")

        user_id = d.pop("userId")

        refresh_token = d.pop("refreshToken", UNSET)

        is_superuser = d.pop("isSuperuser", UNSET)

        authentication = cls(
            access_token=access_token,
            organization_id=organization_id,
            user_id=user_id,
            refresh_token=refresh_token,
            is_superuser=is_superuser,
        )

        authentication.additional_properties = d
        return authentication

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
