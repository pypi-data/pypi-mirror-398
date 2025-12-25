from typing import Any, Dict, List, Type, TypeVar

import attr

T = TypeVar("T", bound="UsagePrices")

@attr.s(auto_attribs=True)
class UsagePrices:
    """
    Attributes:
        data_points (float):
        assets (float):
        bytes_ (float):
        devices (float):
        rtc_turn (float):
        advanced_configuration (float):
        analytics (float):
        customer_portal (float):
        data_export (float):
        data_retention (float):
        support (float):
        teleop (float):
        observability (float):
        share (float):
        mission (float):
        diagnostics (float):
        ssh (float):
        spot (float):
    """

    data_points: float
    assets: float
    bytes_: float
    devices: float
    rtc_turn: float
    advanced_configuration: float
    analytics: float
    customer_portal: float
    data_export: float
    data_retention: float
    support: float
    teleop: float
    observability: float
    share: float
    mission: float
    diagnostics: float
    ssh: float
    spot: float
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        data_points = self.data_points
        assets = self.assets
        bytes_ = self.bytes_
        devices = self.devices
        rtc_turn = self.rtc_turn
        advanced_configuration = self.advanced_configuration
        analytics = self.analytics
        customer_portal = self.customer_portal
        data_export = self.data_export
        data_retention = self.data_retention
        support = self.support
        teleop = self.teleop
        observability = self.observability
        share = self.share
        mission = self.mission
        diagnostics = self.diagnostics
        ssh = self.ssh
        spot = self.spot

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "dataPoints": data_points,
            "assets": assets,
            "bytes": bytes_,
            "devices": devices,
            "rtcTurn": rtc_turn,
            "advancedConfiguration": advanced_configuration,
            "analytics": analytics,
            "customerPortal": customer_portal,
            "dataExport": data_export,
            "dataRetention": data_retention,
            "support": support,
            "teleop": teleop,
            "observability": observability,
            "share": share,
            "mission": mission,
            "diagnostics": diagnostics,
            "ssh": ssh,
            "spot": spot,
        })

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        data_points = d.pop("dataPoints")

        assets = d.pop("assets")

        bytes_ = d.pop("bytes")

        devices = d.pop("devices")

        rtc_turn = d.pop("rtcTurn")

        advanced_configuration = d.pop("advancedConfiguration")

        analytics = d.pop("analytics")

        customer_portal = d.pop("customerPortal")

        data_export = d.pop("dataExport")

        data_retention = d.pop("dataRetention")

        support = d.pop("support")

        teleop = d.pop("teleop")

        observability = d.pop("observability")

        share = d.pop("share")

        mission = d.pop("mission")

        diagnostics = d.pop("diagnostics")

        ssh = d.pop("ssh")

        spot = d.pop("spot")

        usage_prices = cls(
            data_points=data_points,
            assets=assets,
            bytes_=bytes_,
            devices=devices,
            rtc_turn=rtc_turn,
            advanced_configuration=advanced_configuration,
            analytics=analytics,
            customer_portal=customer_portal,
            data_export=data_export,
            data_retention=data_retention,
            support=support,
            teleop=teleop,
            observability=observability,
            share=share,
            mission=mission,
            diagnostics=diagnostics,
            ssh=ssh,
            spot=spot,
        )

        usage_prices.additional_properties = d
        return usage_prices

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
