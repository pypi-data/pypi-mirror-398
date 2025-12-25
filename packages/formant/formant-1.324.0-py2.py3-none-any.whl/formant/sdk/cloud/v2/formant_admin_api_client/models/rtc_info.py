from typing import Any, Dict, List, Type, TypeVar, Union

import attr

from ..models.rtc_info_rtc_ice_server_protocol import \
    RtcInfoRtcIceServerProtocol
from ..models.rtc_info_rtc_ice_transport_policies_item import \
    RtcInfoRtcIceTransportPoliciesItem
from ..types import UNSET, Unset

T = TypeVar("T", bound="RtcInfo")

@attr.s(auto_attribs=True)
class RtcInfo:
    """
    Attributes:
        rtc_ice_transport_policies (Union[Unset, List[RtcInfoRtcIceTransportPoliciesItem]]):
        rtc_ice_server_protocol (Union[Unset, RtcInfoRtcIceServerProtocol]):
        use_all_servers (Union[Unset, bool]):
    """

    rtc_ice_transport_policies: Union[Unset, List[RtcInfoRtcIceTransportPoliciesItem]] = UNSET
    rtc_ice_server_protocol: Union[Unset, RtcInfoRtcIceServerProtocol] = UNSET
    use_all_servers: Union[Unset, bool] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        rtc_ice_transport_policies: Union[Unset, List[str]] = UNSET
        if not isinstance(self.rtc_ice_transport_policies, Unset):
            rtc_ice_transport_policies = []
            for rtc_ice_transport_policies_item_data in self.rtc_ice_transport_policies:
                rtc_ice_transport_policies_item = rtc_ice_transport_policies_item_data.value

                rtc_ice_transport_policies.append(rtc_ice_transport_policies_item)




        rtc_ice_server_protocol: Union[Unset, str] = UNSET
        if not isinstance(self.rtc_ice_server_protocol, Unset):
            rtc_ice_server_protocol = self.rtc_ice_server_protocol.value

        use_all_servers = self.use_all_servers

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
        })
        if rtc_ice_transport_policies is not UNSET:
            field_dict["rtcIceTransportPolicies"] = rtc_ice_transport_policies
        if rtc_ice_server_protocol is not UNSET:
            field_dict["rtcIceServerProtocol"] = rtc_ice_server_protocol
        if use_all_servers is not UNSET:
            field_dict["useAllServers"] = use_all_servers

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        rtc_ice_transport_policies = []
        _rtc_ice_transport_policies = d.pop("rtcIceTransportPolicies", UNSET)
        for rtc_ice_transport_policies_item_data in (_rtc_ice_transport_policies or []):
            rtc_ice_transport_policies_item = RtcInfoRtcIceTransportPoliciesItem(rtc_ice_transport_policies_item_data)



            rtc_ice_transport_policies.append(rtc_ice_transport_policies_item)


        _rtc_ice_server_protocol = d.pop("rtcIceServerProtocol", UNSET)
        rtc_ice_server_protocol: Union[Unset, RtcInfoRtcIceServerProtocol]
        if isinstance(_rtc_ice_server_protocol,  Unset):
            rtc_ice_server_protocol = UNSET
        else:
            rtc_ice_server_protocol = RtcInfoRtcIceServerProtocol(_rtc_ice_server_protocol)




        use_all_servers = d.pop("useAllServers", UNSET)

        rtc_info = cls(
            rtc_ice_transport_policies=rtc_ice_transport_policies,
            rtc_ice_server_protocol=rtc_ice_server_protocol,
            use_all_servers=use_all_servers,
        )

        rtc_info.additional_properties = d
        return rtc_info

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
