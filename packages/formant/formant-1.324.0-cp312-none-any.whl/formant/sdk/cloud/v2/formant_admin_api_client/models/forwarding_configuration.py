from typing import Any, Dict, List, Type, TypeVar, Union, cast

import attr

from ..types import UNSET, Unset

T = TypeVar("T", bound="ForwardingConfiguration")

@attr.s(auto_attribs=True)
class ForwardingConfiguration:
    """
    Attributes:
        pagerduty (Union[Unset, bool]):
        slack_channels (Union[Unset, List[str]]):
        webhooks (Union[Unset, List[str]]):
        sms (Union[Unset, bool]):
        slack (Union[Unset, bool]):
        device_slack_channels (Union[Unset, bool]):
    """

    pagerduty: Union[Unset, bool] = UNSET
    slack_channels: Union[Unset, List[str]] = UNSET
    webhooks: Union[Unset, List[str]] = UNSET
    sms: Union[Unset, bool] = UNSET
    slack: Union[Unset, bool] = UNSET
    device_slack_channels: Union[Unset, bool] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        pagerduty = self.pagerduty
        slack_channels: Union[Unset, List[str]] = UNSET
        if not isinstance(self.slack_channels, Unset):
            slack_channels = self.slack_channels




        webhooks: Union[Unset, List[str]] = UNSET
        if not isinstance(self.webhooks, Unset):
            webhooks = self.webhooks




        sms = self.sms
        slack = self.slack
        device_slack_channels = self.device_slack_channels

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
        })
        if pagerduty is not UNSET:
            field_dict["pagerduty"] = pagerduty
        if slack_channels is not UNSET:
            field_dict["slackChannels"] = slack_channels
        if webhooks is not UNSET:
            field_dict["webhooks"] = webhooks
        if sms is not UNSET:
            field_dict["sms"] = sms
        if slack is not UNSET:
            field_dict["slack"] = slack
        if device_slack_channels is not UNSET:
            field_dict["deviceSlackChannels"] = device_slack_channels

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        pagerduty = d.pop("pagerduty", UNSET)

        slack_channels = cast(List[str], d.pop("slackChannels", UNSET))


        webhooks = cast(List[str], d.pop("webhooks", UNSET))


        sms = d.pop("sms", UNSET)

        slack = d.pop("slack", UNSET)

        device_slack_channels = d.pop("deviceSlackChannels", UNSET)

        forwarding_configuration = cls(
            pagerduty=pagerduty,
            slack_channels=slack_channels,
            webhooks=webhooks,
            sms=sms,
            slack=slack,
            device_slack_channels=device_slack_channels,
        )

        forwarding_configuration.additional_properties = d
        return forwarding_configuration

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
