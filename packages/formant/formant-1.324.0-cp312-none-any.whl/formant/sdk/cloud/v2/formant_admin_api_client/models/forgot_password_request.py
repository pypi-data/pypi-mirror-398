from typing import Any, Dict, List, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

T = TypeVar("T", bound="ForgotPasswordRequest")

@attr.s(auto_attribs=True)
class ForgotPasswordRequest:
    """
    Attributes:
        email (str): Email address to which to send a 'forgot password?' email.
        email_configuration_id (Union[Unset, str]): ID of the custom email template you want to use for the 'forgot
            password?' email.
    """

    email: str
    email_configuration_id: Union[Unset, str] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        email = self.email
        email_configuration_id = self.email_configuration_id

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "email": email,
        })
        if email_configuration_id is not UNSET:
            field_dict["emailConfigurationId"] = email_configuration_id

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        email = d.pop("email")

        email_configuration_id = d.pop("emailConfigurationId", UNSET)

        forgot_password_request = cls(
            email=email,
            email_configuration_id=email_configuration_id,
        )

        forgot_password_request.additional_properties = d
        return forgot_password_request

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
