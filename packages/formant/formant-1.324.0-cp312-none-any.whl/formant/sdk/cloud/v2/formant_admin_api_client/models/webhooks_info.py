from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar

import attr

if TYPE_CHECKING:
  from ..models.webhook import Webhook




T = TypeVar("T", bound="WebhooksInfo")

@attr.s(auto_attribs=True)
class WebhooksInfo:
    """
    Attributes:
        webhooks (List['Webhook']):
    """

    webhooks: List['Webhook']
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        webhooks = []
        for webhooks_item_data in self.webhooks:
            webhooks_item = webhooks_item_data.to_dict()

            webhooks.append(webhooks_item)





        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "webhooks": webhooks,
        })

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.webhook import Webhook
        d = src_dict.copy()
        webhooks = []
        _webhooks = d.pop("webhooks")
        for webhooks_item_data in (_webhooks):
            webhooks_item = Webhook.from_dict(webhooks_item_data)



            webhooks.append(webhooks_item)


        webhooks_info = cls(
            webhooks=webhooks,
        )

        webhooks_info.additional_properties = d
        return webhooks_info

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
