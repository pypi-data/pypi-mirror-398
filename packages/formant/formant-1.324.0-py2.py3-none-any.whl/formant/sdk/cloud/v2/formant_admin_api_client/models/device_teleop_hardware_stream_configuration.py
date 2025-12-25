from typing import Any, Dict, List, Type, TypeVar, Union

import attr

from ..models.device_teleop_hardware_stream_configuration_hardware_type import \
    DeviceTeleopHardwareStreamConfigurationHardwareType
from ..models.device_teleop_hardware_stream_configuration_mode import \
    DeviceTeleopHardwareStreamConfigurationMode
from ..models.device_teleop_hardware_stream_configuration_quality import \
    DeviceTeleopHardwareStreamConfigurationQuality
from ..models.device_teleop_hardware_stream_configuration_rtc_stream_type import \
    DeviceTeleopHardwareStreamConfigurationRtcStreamType
from ..types import UNSET, Unset

T = TypeVar("T", bound="DeviceTeleopHardwareStreamConfiguration")

@attr.s(auto_attribs=True)
class DeviceTeleopHardwareStreamConfiguration:
    """
    Attributes:
        name (str):
        rtc_stream_type (DeviceTeleopHardwareStreamConfigurationRtcStreamType):
        mode (DeviceTeleopHardwareStreamConfigurationMode):
        hw_descriptor (str):
        hardware_type (DeviceTeleopHardwareStreamConfigurationHardwareType):
        quality (DeviceTeleopHardwareStreamConfigurationQuality):
        label (Union[Unset, str]):
        rtsp_encoding_needed (Union[Unset, bool]):
        is_onvif (Union[Unset, bool]):
        ip_cam_username (Union[Unset, str]):
        ip_cam_password (Union[Unset, str]):
        overlay_clock (Union[Unset, bool]):
        bitrate (Union[Unset, int]):
        disable_adaptive_quality (Union[Unset, bool]):
    """

    name: str
    rtc_stream_type: DeviceTeleopHardwareStreamConfigurationRtcStreamType
    mode: DeviceTeleopHardwareStreamConfigurationMode
    hw_descriptor: str
    hardware_type: DeviceTeleopHardwareStreamConfigurationHardwareType
    quality: DeviceTeleopHardwareStreamConfigurationQuality
    label: Union[Unset, str] = UNSET
    rtsp_encoding_needed: Union[Unset, bool] = UNSET
    is_onvif: Union[Unset, bool] = UNSET
    ip_cam_username: Union[Unset, str] = UNSET
    ip_cam_password: Union[Unset, str] = UNSET
    overlay_clock: Union[Unset, bool] = UNSET
    bitrate: Union[Unset, int] = UNSET
    disable_adaptive_quality: Union[Unset, bool] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        name = self.name
        rtc_stream_type = self.rtc_stream_type.value

        mode = self.mode.value

        hw_descriptor = self.hw_descriptor
        hardware_type = self.hardware_type.value

        quality = self.quality.value

        label = self.label
        rtsp_encoding_needed = self.rtsp_encoding_needed
        is_onvif = self.is_onvif
        ip_cam_username = self.ip_cam_username
        ip_cam_password = self.ip_cam_password
        overlay_clock = self.overlay_clock
        bitrate = self.bitrate
        disable_adaptive_quality = self.disable_adaptive_quality

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "name": name,
            "rtcStreamType": rtc_stream_type,
            "mode": mode,
            "hwDescriptor": hw_descriptor,
            "hardwareType": hardware_type,
            "quality": quality,
        })
        if label is not UNSET:
            field_dict["label"] = label
        if rtsp_encoding_needed is not UNSET:
            field_dict["rtspEncodingNeeded"] = rtsp_encoding_needed
        if is_onvif is not UNSET:
            field_dict["isOnvif"] = is_onvif
        if ip_cam_username is not UNSET:
            field_dict["ipCamUsername"] = ip_cam_username
        if ip_cam_password is not UNSET:
            field_dict["ipCamPassword"] = ip_cam_password
        if overlay_clock is not UNSET:
            field_dict["overlayClock"] = overlay_clock
        if bitrate is not UNSET:
            field_dict["bitrate"] = bitrate
        if disable_adaptive_quality is not UNSET:
            field_dict["disableAdaptiveQuality"] = disable_adaptive_quality

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        name = d.pop("name")

        rtc_stream_type = DeviceTeleopHardwareStreamConfigurationRtcStreamType(d.pop("rtcStreamType"))




        mode = DeviceTeleopHardwareStreamConfigurationMode(d.pop("mode"))




        hw_descriptor = d.pop("hwDescriptor")

        hardware_type = DeviceTeleopHardwareStreamConfigurationHardwareType(d.pop("hardwareType"))




        quality = DeviceTeleopHardwareStreamConfigurationQuality(d.pop("quality"))




        label = d.pop("label", UNSET)

        rtsp_encoding_needed = d.pop("rtspEncodingNeeded", UNSET)

        is_onvif = d.pop("isOnvif", UNSET)

        ip_cam_username = d.pop("ipCamUsername", UNSET)

        ip_cam_password = d.pop("ipCamPassword", UNSET)

        overlay_clock = d.pop("overlayClock", UNSET)

        bitrate = d.pop("bitrate", UNSET)

        disable_adaptive_quality = d.pop("disableAdaptiveQuality", UNSET)

        device_teleop_hardware_stream_configuration = cls(
            name=name,
            rtc_stream_type=rtc_stream_type,
            mode=mode,
            hw_descriptor=hw_descriptor,
            hardware_type=hardware_type,
            quality=quality,
            label=label,
            rtsp_encoding_needed=rtsp_encoding_needed,
            is_onvif=is_onvif,
            ip_cam_username=ip_cam_username,
            ip_cam_password=ip_cam_password,
            overlay_clock=overlay_clock,
            bitrate=bitrate,
            disable_adaptive_quality=disable_adaptive_quality,
        )

        device_teleop_hardware_stream_configuration.additional_properties = d
        return device_teleop_hardware_stream_configuration

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
