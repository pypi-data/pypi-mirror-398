from typing import Any, Dict, List, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

T = TypeVar("T", bound="CheckSsoRequest")

@attr.s(auto_attribs=True)
class CheckSsoRequest:
    """
    Attributes:
        email (str): Email address of the account whose SSO configuration you want to inspect.
        allow_user_auto_creation (Union[Unset, bool]): Currently unused, ignore.
    """

    email: str
    allow_user_auto_creation: Union[Unset, bool] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        email = self.email
        allow_user_auto_creation = self.allow_user_auto_creation

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "email": email,
        })
        if allow_user_auto_creation is not UNSET:
            field_dict["allowUserAutoCreation"] = allow_user_auto_creation

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        email = d.pop("email")

        allow_user_auto_creation = d.pop("allowUserAutoCreation", UNSET)

        check_sso_request = cls(
            email=email,
            allow_user_auto_creation=allow_user_auto_creation,
        )

        check_sso_request.additional_properties = d
        return check_sso_request

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
