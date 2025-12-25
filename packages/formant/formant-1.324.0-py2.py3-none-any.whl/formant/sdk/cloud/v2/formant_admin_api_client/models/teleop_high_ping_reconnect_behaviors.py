from typing import Any, Dict, List, Type, TypeVar

import attr

T = TypeVar("T", bound="TeleopHighPingReconnectBehaviors")

@attr.s(auto_attribs=True)
class TeleopHighPingReconnectBehaviors:
    """
    Attributes:
        enabled (bool):
        max_ping_threshold (float):
        max_high_ping_warning_periods (float):
        recovery_threshhold (float):
        max_ping_disconnect_periods (float):
        max_ping_disconnect_threshold (float):
        should_retry (bool):
        loss_threshold (float):
        high_loss_periods (float):
    """

    enabled: bool
    max_ping_threshold: float
    max_high_ping_warning_periods: float
    recovery_threshhold: float
    max_ping_disconnect_periods: float
    max_ping_disconnect_threshold: float
    should_retry: bool
    loss_threshold: float
    high_loss_periods: float
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        enabled = self.enabled
        max_ping_threshold = self.max_ping_threshold
        max_high_ping_warning_periods = self.max_high_ping_warning_periods
        recovery_threshhold = self.recovery_threshhold
        max_ping_disconnect_periods = self.max_ping_disconnect_periods
        max_ping_disconnect_threshold = self.max_ping_disconnect_threshold
        should_retry = self.should_retry
        loss_threshold = self.loss_threshold
        high_loss_periods = self.high_loss_periods

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "enabled": enabled,
            "maxPingThreshold": max_ping_threshold,
            "maxHighPingWarningPeriods": max_high_ping_warning_periods,
            "recoveryThreshhold": recovery_threshhold,
            "maxPingDisconnectPeriods": max_ping_disconnect_periods,
            "maxPingDisconnectThreshold": max_ping_disconnect_threshold,
            "shouldRetry": should_retry,
            "lossThreshold": loss_threshold,
            "highLossPeriods": high_loss_periods,
        })

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        enabled = d.pop("enabled")

        max_ping_threshold = d.pop("maxPingThreshold")

        max_high_ping_warning_periods = d.pop("maxHighPingWarningPeriods")

        recovery_threshhold = d.pop("recoveryThreshhold")

        max_ping_disconnect_periods = d.pop("maxPingDisconnectPeriods")

        max_ping_disconnect_threshold = d.pop("maxPingDisconnectThreshold")

        should_retry = d.pop("shouldRetry")

        loss_threshold = d.pop("lossThreshold")

        high_loss_periods = d.pop("highLossPeriods")

        teleop_high_ping_reconnect_behaviors = cls(
            enabled=enabled,
            max_ping_threshold=max_ping_threshold,
            max_high_ping_warning_periods=max_high_ping_warning_periods,
            recovery_threshhold=recovery_threshhold,
            max_ping_disconnect_periods=max_ping_disconnect_periods,
            max_ping_disconnect_threshold=max_ping_disconnect_threshold,
            should_retry=should_retry,
            loss_threshold=loss_threshold,
            high_loss_periods=high_loss_periods,
        )

        teleop_high_ping_reconnect_behaviors.additional_properties = d
        return teleop_high_ping_reconnect_behaviors

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
