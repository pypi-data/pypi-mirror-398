from typing import Any, Dict, List, Type, TypeVar

import attr

T = TypeVar("T", bound="ChangePasswordRequest")

@attr.s(auto_attribs=True)
class ChangePasswordRequest:
    """
    Attributes:
        current_password (str): Enter your current Formant password.
        new_password (str): Enter your new Formant password.
        refresh_token (str): Enter the refresh token you received when you logged in.
    """

    current_password: str
    new_password: str
    refresh_token: str
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        current_password = self.current_password
        new_password = self.new_password
        refresh_token = self.refresh_token

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "currentPassword": current_password,
            "newPassword": new_password,
            "refreshToken": refresh_token,
        })

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        current_password = d.pop("currentPassword")

        new_password = d.pop("newPassword")

        refresh_token = d.pop("refreshToken")

        change_password_request = cls(
            current_password=current_password,
            new_password=new_password,
            refresh_token=refresh_token,
        )

        change_password_request.additional_properties = d
        return change_password_request

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
