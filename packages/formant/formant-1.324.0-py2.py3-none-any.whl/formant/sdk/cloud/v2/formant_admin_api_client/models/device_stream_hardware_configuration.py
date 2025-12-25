from typing import Any, Dict, List, Type, TypeVar, Union

import attr

from ..models.device_stream_hardware_configuration_hardware_type import \
    DeviceStreamHardwareConfigurationHardwareType
from ..models.device_stream_hardware_configuration_quality import \
    DeviceStreamHardwareConfigurationQuality
from ..models.device_stream_hardware_configuration_type import \
    DeviceStreamHardwareConfigurationType
from ..types import UNSET, Unset

T = TypeVar("T", bound="DeviceStreamHardwareConfiguration")

@attr.s(auto_attribs=True)
class DeviceStreamHardwareConfiguration:
    """
    Attributes:
        type (DeviceStreamHardwareConfigurationType):
        hw_descriptor (str):
        hardware_type (DeviceStreamHardwareConfigurationHardwareType):
        audio_hw_descriptor (Union[Unset, str]):
        rtsp_encoding_needed (Union[Unset, bool]):
        is_onvif (Union[Unset, bool]):
        overlay_clock (Union[Unset, bool]):
        ip_cam_username (Union[Unset, str]):
        ip_cam_password (Union[Unset, str]):
        bitrate (Union[Unset, int]):
        disable_adaptive_quality (Union[Unset, bool]):
        quality (Union[Unset, DeviceStreamHardwareConfigurationQuality]):
    """

    type: DeviceStreamHardwareConfigurationType
    hw_descriptor: str
    hardware_type: DeviceStreamHardwareConfigurationHardwareType
    audio_hw_descriptor: Union[Unset, str] = UNSET
    rtsp_encoding_needed: Union[Unset, bool] = UNSET
    is_onvif: Union[Unset, bool] = UNSET
    overlay_clock: Union[Unset, bool] = UNSET
    ip_cam_username: Union[Unset, str] = UNSET
    ip_cam_password: Union[Unset, str] = UNSET
    bitrate: Union[Unset, int] = UNSET
    disable_adaptive_quality: Union[Unset, bool] = UNSET
    quality: Union[Unset, DeviceStreamHardwareConfigurationQuality] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        type = self.type.value

        hw_descriptor = self.hw_descriptor
        hardware_type = self.hardware_type.value

        audio_hw_descriptor = self.audio_hw_descriptor
        rtsp_encoding_needed = self.rtsp_encoding_needed
        is_onvif = self.is_onvif
        overlay_clock = self.overlay_clock
        ip_cam_username = self.ip_cam_username
        ip_cam_password = self.ip_cam_password
        bitrate = self.bitrate
        disable_adaptive_quality = self.disable_adaptive_quality
        quality: Union[Unset, str] = UNSET
        if not isinstance(self.quality, Unset):
            quality = self.quality.value


        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "type": type,
            "hwDescriptor": hw_descriptor,
            "hardwareType": hardware_type,
        })
        if audio_hw_descriptor is not UNSET:
            field_dict["audioHwDescriptor"] = audio_hw_descriptor
        if rtsp_encoding_needed is not UNSET:
            field_dict["rtspEncodingNeeded"] = rtsp_encoding_needed
        if is_onvif is not UNSET:
            field_dict["isOnvif"] = is_onvif
        if overlay_clock is not UNSET:
            field_dict["overlayClock"] = overlay_clock
        if ip_cam_username is not UNSET:
            field_dict["ipCamUsername"] = ip_cam_username
        if ip_cam_password is not UNSET:
            field_dict["ipCamPassword"] = ip_cam_password
        if bitrate is not UNSET:
            field_dict["bitrate"] = bitrate
        if disable_adaptive_quality is not UNSET:
            field_dict["disableAdaptiveQuality"] = disable_adaptive_quality
        if quality is not UNSET:
            field_dict["quality"] = quality

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        type = DeviceStreamHardwareConfigurationType(d.pop("type"))




        hw_descriptor = d.pop("hwDescriptor")

        hardware_type = DeviceStreamHardwareConfigurationHardwareType(d.pop("hardwareType"))




        audio_hw_descriptor = d.pop("audioHwDescriptor", UNSET)

        rtsp_encoding_needed = d.pop("rtspEncodingNeeded", UNSET)

        is_onvif = d.pop("isOnvif", UNSET)

        overlay_clock = d.pop("overlayClock", UNSET)

        ip_cam_username = d.pop("ipCamUsername", UNSET)

        ip_cam_password = d.pop("ipCamPassword", UNSET)

        bitrate = d.pop("bitrate", UNSET)

        disable_adaptive_quality = d.pop("disableAdaptiveQuality", UNSET)

        _quality = d.pop("quality", UNSET)
        quality: Union[Unset, DeviceStreamHardwareConfigurationQuality]
        if isinstance(_quality,  Unset):
            quality = UNSET
        else:
            quality = DeviceStreamHardwareConfigurationQuality(_quality)




        device_stream_hardware_configuration = cls(
            type=type,
            hw_descriptor=hw_descriptor,
            hardware_type=hardware_type,
            audio_hw_descriptor=audio_hw_descriptor,
            rtsp_encoding_needed=rtsp_encoding_needed,
            is_onvif=is_onvif,
            overlay_clock=overlay_clock,
            ip_cam_username=ip_cam_username,
            ip_cam_password=ip_cam_password,
            bitrate=bitrate,
            disable_adaptive_quality=disable_adaptive_quality,
            quality=quality,
        )

        device_stream_hardware_configuration.additional_properties = d
        return device_stream_hardware_configuration

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
