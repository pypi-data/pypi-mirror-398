from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

if TYPE_CHECKING:
  from ..models.webhook_headers import WebhookHeaders




T = TypeVar("T", bound="Webhook")

@attr.s(auto_attribs=True)
class Webhook:
    """
    Attributes:
        name (Any):
        url (str):
        headers (Union[Unset, WebhookHeaders]):
    """

    name: Any
    url: str
    headers: Union[Unset, 'WebhookHeaders'] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        name = self.name
        url = self.url
        headers: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.headers, Unset):
            headers = self.headers.to_dict()


        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "name": name,
            "url": url,
        })
        if headers is not UNSET:
            field_dict["headers"] = headers

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.webhook_headers import WebhookHeaders
        d = src_dict.copy()
        name = d.pop("name")

        url = d.pop("url")

        _headers = d.pop("headers", UNSET)
        headers: Union[Unset, WebhookHeaders]
        if isinstance(_headers,  Unset):
            headers = UNSET
        else:
            headers = WebhookHeaders.from_dict(_headers)




        webhook = cls(
            name=name,
            url=url,
            headers=headers,
        )

        webhook.additional_properties = d
        return webhook

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
