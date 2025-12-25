from typing import Any, Dict, List, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

T = TypeVar("T", bound="RefreshRequest")

@attr.s(auto_attribs=True)
class RefreshRequest:
    """
    Attributes:
        refresh_token (str):
        token_expiration_seconds (Union[Unset, int]):
    """

    refresh_token: str
    token_expiration_seconds: Union[Unset, int] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        refresh_token = self.refresh_token
        token_expiration_seconds = self.token_expiration_seconds

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "refreshToken": refresh_token,
        })
        if token_expiration_seconds is not UNSET:
            field_dict["tokenExpirationSeconds"] = token_expiration_seconds

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        refresh_token = d.pop("refreshToken")

        token_expiration_seconds = d.pop("tokenExpirationSeconds", UNSET)

        refresh_request = cls(
            refresh_token=refresh_token,
            token_expiration_seconds=token_expiration_seconds,
        )

        refresh_request.additional_properties = d
        return refresh_request

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
