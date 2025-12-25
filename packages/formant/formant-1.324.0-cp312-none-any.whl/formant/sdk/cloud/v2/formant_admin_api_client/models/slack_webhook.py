from typing import Any, Dict, List, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

T = TypeVar("T", bound="SlackWebhook")

@attr.s(auto_attribs=True)
class SlackWebhook:
    """
    Attributes:
        webhook_url (str):
        webhook_channel (str):
        configuration_url (str):
        team_id (Union[Unset, str]):
        token (Union[Unset, str]):
    """

    webhook_url: str
    webhook_channel: str
    configuration_url: str
    team_id: Union[Unset, str] = UNSET
    token: Union[Unset, str] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        webhook_url = self.webhook_url
        webhook_channel = self.webhook_channel
        configuration_url = self.configuration_url
        team_id = self.team_id
        token = self.token

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "webhookUrl": webhook_url,
            "webhookChannel": webhook_channel,
            "configurationUrl": configuration_url,
        })
        if team_id is not UNSET:
            field_dict["teamId"] = team_id
        if token is not UNSET:
            field_dict["token"] = token

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        webhook_url = d.pop("webhookUrl")

        webhook_channel = d.pop("webhookChannel")

        configuration_url = d.pop("configurationUrl")

        team_id = d.pop("teamId", UNSET)

        token = d.pop("token", UNSET)

        slack_webhook = cls(
            webhook_url=webhook_url,
            webhook_channel=webhook_channel,
            configuration_url=configuration_url,
            team_id=team_id,
            token=token,
        )

        slack_webhook.additional_properties = d
        return slack_webhook

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
