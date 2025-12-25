import datetime
from typing import Any, Dict, List, Type, TypeVar

import attr
from dateutil.parser import isoparse

T = TypeVar("T", bound="GoogleInfo")

@attr.s(auto_attribs=True)
class GoogleInfo:
    """
    Attributes:
        refresh_token (str):
        access_token (str):
        expiration_date (datetime.datetime):
        scope (str):
    """

    refresh_token: str
    access_token: str
    expiration_date: datetime.datetime
    scope: str
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        refresh_token = self.refresh_token
        access_token = self.access_token
        expiration_date = self.expiration_date.isoformat()

        scope = self.scope

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "refreshToken": refresh_token,
            "accessToken": access_token,
            "expirationDate": expiration_date,
            "scope": scope,
        })

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        refresh_token = d.pop("refreshToken")

        access_token = d.pop("accessToken")

        expiration_date = isoparse(d.pop("expirationDate"))




        scope = d.pop("scope")

        google_info = cls(
            refresh_token=refresh_token,
            access_token=access_token,
            expiration_date=expiration_date,
            scope=scope,
        )

        google_info.additional_properties = d
        return google_info

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
