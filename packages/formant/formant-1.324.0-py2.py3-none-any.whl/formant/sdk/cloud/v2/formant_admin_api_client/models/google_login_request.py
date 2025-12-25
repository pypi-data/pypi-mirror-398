from typing import Any, Dict, List, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

T = TypeVar("T", bound="GoogleLoginRequest")

@attr.s(auto_attribs=True)
class GoogleLoginRequest:
    """
    Attributes:
        token (str):
        auto_create_org (Union[Unset, bool]):
    """

    token: str
    auto_create_org: Union[Unset, bool] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        token = self.token
        auto_create_org = self.auto_create_org

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "token": token,
        })
        if auto_create_org is not UNSET:
            field_dict["autoCreateOrg"] = auto_create_org

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        token = d.pop("token")

        auto_create_org = d.pop("autoCreateOrg", UNSET)

        google_login_request = cls(
            token=token,
            auto_create_org=auto_create_org,
        )

        google_login_request.additional_properties = d
        return google_login_request

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
