from typing import Any, Dict, List, Type, TypeVar

import attr

T = TypeVar("T", bound="CheckSsoResult")

@attr.s(auto_attribs=True)
class CheckSsoResult:
    """
    Attributes:
        issuer (str):
        client_id (str):
        is_sso (bool):
    """

    issuer: str
    client_id: str
    is_sso: bool
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        issuer = self.issuer
        client_id = self.client_id
        is_sso = self.is_sso

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "issuer": issuer,
            "clientId": client_id,
            "isSso": is_sso,
        })

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        issuer = d.pop("issuer")

        client_id = d.pop("clientId")

        is_sso = d.pop("isSso")

        check_sso_result = cls(
            issuer=issuer,
            client_id=client_id,
            is_sso=is_sso,
        )

        check_sso_result.additional_properties = d
        return check_sso_result

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
