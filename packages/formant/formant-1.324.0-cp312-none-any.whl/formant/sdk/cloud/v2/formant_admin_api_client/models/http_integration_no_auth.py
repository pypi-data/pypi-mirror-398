from typing import Any, Dict, List, Type, TypeVar

import attr

from ..models.http_integration_no_auth_type import HttpIntegrationNoAuthType

T = TypeVar("T", bound="HttpIntegrationNoAuth")

@attr.s(auto_attribs=True)
class HttpIntegrationNoAuth:
    """
    Attributes:
        type (HttpIntegrationNoAuthType):
    """

    type: HttpIntegrationNoAuthType
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        type = self.type.value


        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "type": type,
        })

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        type = HttpIntegrationNoAuthType(d.pop("type"))




        http_integration_no_auth = cls(
            type=type,
        )

        http_integration_no_auth.additional_properties = d
        return http_integration_no_auth

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
