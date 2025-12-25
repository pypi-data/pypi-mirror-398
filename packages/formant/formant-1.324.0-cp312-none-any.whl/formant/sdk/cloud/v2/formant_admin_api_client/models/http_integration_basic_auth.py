from typing import Any, Dict, List, Type, TypeVar

import attr

from ..models.http_integration_basic_auth_type import \
    HttpIntegrationBasicAuthType

T = TypeVar("T", bound="HttpIntegrationBasicAuth")

@attr.s(auto_attribs=True)
class HttpIntegrationBasicAuth:
    """
    Attributes:
        type (HttpIntegrationBasicAuthType):
        username (str):
        password (str):
    """

    type: HttpIntegrationBasicAuthType
    username: str
    password: str
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        type = self.type.value

        username = self.username
        password = self.password

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "type": type,
            "username": username,
            "password": password,
        })

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        type = HttpIntegrationBasicAuthType(d.pop("type"))




        username = d.pop("username")

        password = d.pop("password")

        http_integration_basic_auth = cls(
            type=type,
            username=username,
            password=password,
        )

        http_integration_basic_auth.additional_properties = d
        return http_integration_basic_auth

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
