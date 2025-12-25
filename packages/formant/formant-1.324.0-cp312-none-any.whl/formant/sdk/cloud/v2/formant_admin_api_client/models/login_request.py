from typing import Any, Dict, List, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

T = TypeVar("T", bound="LoginRequest")

@attr.s(auto_attribs=True)
class LoginRequest:
    """
    Attributes:
        email (str): Enter the email address associated with your Formant account.
        password (str): Enter the password associated with your Formant account.
        token_expiration_seconds (Union[Unset, int]): How long you want this authentication token to be valid (default 1
            hour).
    """

    email: str
    password: str
    token_expiration_seconds: Union[Unset, int] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        email = self.email
        password = self.password
        token_expiration_seconds = self.token_expiration_seconds

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "email": email,
            "password": password,
        })
        if token_expiration_seconds is not UNSET:
            field_dict["tokenExpirationSeconds"] = token_expiration_seconds

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        email = d.pop("email")

        password = d.pop("password")

        token_expiration_seconds = d.pop("tokenExpirationSeconds", UNSET)

        login_request = cls(
            email=email,
            password=password,
            token_expiration_seconds=token_expiration_seconds,
        )

        login_request.additional_properties = d
        return login_request

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
