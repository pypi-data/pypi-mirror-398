from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

if TYPE_CHECKING:
  from ..models.slack_webhook import SlackWebhook




T = TypeVar("T", bound="SlackInfo")

@attr.s(auto_attribs=True)
class SlackInfo:
    """
    Attributes:
        webhooks (Union[Unset, List['SlackWebhook']]):
        webhook_url (Union[Unset, str]):
        webhook_channel (Union[Unset, str]):
        configuration_url (Union[Unset, str]):
        team_id (Union[Unset, str]):
        token (Union[Unset, str]):
    """

    webhooks: Union[Unset, List['SlackWebhook']] = UNSET
    webhook_url: Union[Unset, str] = UNSET
    webhook_channel: Union[Unset, str] = UNSET
    configuration_url: Union[Unset, str] = UNSET
    team_id: Union[Unset, str] = UNSET
    token: Union[Unset, str] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        webhooks: Union[Unset, List[Dict[str, Any]]] = UNSET
        if not isinstance(self.webhooks, Unset):
            webhooks = []
            for webhooks_item_data in self.webhooks:
                webhooks_item = webhooks_item_data.to_dict()

                webhooks.append(webhooks_item)




        webhook_url = self.webhook_url
        webhook_channel = self.webhook_channel
        configuration_url = self.configuration_url
        team_id = self.team_id
        token = self.token

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
        })
        if webhooks is not UNSET:
            field_dict["webhooks"] = webhooks
        if webhook_url is not UNSET:
            field_dict["webhookUrl"] = webhook_url
        if webhook_channel is not UNSET:
            field_dict["webhookChannel"] = webhook_channel
        if configuration_url is not UNSET:
            field_dict["configurationUrl"] = configuration_url
        if team_id is not UNSET:
            field_dict["teamId"] = team_id
        if token is not UNSET:
            field_dict["token"] = token

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.slack_webhook import SlackWebhook
        d = src_dict.copy()
        webhooks = []
        _webhooks = d.pop("webhooks", UNSET)
        for webhooks_item_data in (_webhooks or []):
            webhooks_item = SlackWebhook.from_dict(webhooks_item_data)



            webhooks.append(webhooks_item)


        webhook_url = d.pop("webhookUrl", UNSET)

        webhook_channel = d.pop("webhookChannel", UNSET)

        configuration_url = d.pop("configurationUrl", UNSET)

        team_id = d.pop("teamId", UNSET)

        token = d.pop("token", UNSET)

        slack_info = cls(
            webhooks=webhooks,
            webhook_url=webhook_url,
            webhook_channel=webhook_channel,
            configuration_url=configuration_url,
            team_id=team_id,
            token=token,
        )

        slack_info.additional_properties = d
        return slack_info

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
