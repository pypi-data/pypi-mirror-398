from typing import Any, Dict, List, Type, TypeVar

import attr

T = TypeVar("T", bound="PagerdutyInfo")

@attr.s(auto_attribs=True)
class PagerdutyInfo:
    """
    Attributes:
        account (str):
        service_name (str):
        service_key (str):
    """

    account: str
    service_name: str
    service_key: str
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        account = self.account
        service_name = self.service_name
        service_key = self.service_key

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "account": account,
            "serviceName": service_name,
            "serviceKey": service_key,
        })

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        account = d.pop("account")

        service_name = d.pop("serviceName")

        service_key = d.pop("serviceKey")

        pagerduty_info = cls(
            account=account,
            service_name=service_name,
            service_key=service_key,
        )

        pagerduty_info.additional_properties = d
        return pagerduty_info

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
