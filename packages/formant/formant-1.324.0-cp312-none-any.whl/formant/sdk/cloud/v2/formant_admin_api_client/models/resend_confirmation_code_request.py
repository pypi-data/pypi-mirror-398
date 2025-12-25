from typing import Any, Dict, List, Type, TypeVar

import attr

T = TypeVar("T", bound="ResendConfirmationCodeRequest")

@attr.s(auto_attribs=True)
class ResendConfirmationCodeRequest:
    """
    Attributes:
        email (str): Email address to which you want to resend the confirmation code to join a Formant organization.
    """

    email: str
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        email = self.email

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "email": email,
        })

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        email = d.pop("email")

        resend_confirmation_code_request = cls(
            email=email,
        )

        resend_confirmation_code_request.additional_properties = d
        return resend_confirmation_code_request

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
