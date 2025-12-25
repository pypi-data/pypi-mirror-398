from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

if TYPE_CHECKING:
  from ..models.audio_device import AudioDevice
  from ..models.kernel_info import KernelInfo
  from ..models.network_info import NetworkInfo
  from ..models.node_info import NodeInfo
  from ..models.onvif_device import OnvifDevice
  from ..models.os_info import OsInfo
  from ..models.video_device import VideoDevice




T = TypeVar("T", bound="HwInfo")

@attr.s(auto_attribs=True)
class HwInfo:
    """
    Attributes:
        kernel_info (Union[Unset, KernelInfo]):
        os_info (Union[Unset, OsInfo]):
        node_info (Union[Unset, NodeInfo]):
        network_info (Union[Unset, NetworkInfo]):
        hw_encoding_available (Union[Unset, bool]):
        video_devices (Union[Unset, List['VideoDevice']]):
        audio_capture_devices (Union[Unset, List['AudioDevice']]):
        onvif_devices (Union[Unset, List['OnvifDevice']]):
    """

    kernel_info: Union[Unset, 'KernelInfo'] = UNSET
    os_info: Union[Unset, 'OsInfo'] = UNSET
    node_info: Union[Unset, 'NodeInfo'] = UNSET
    network_info: Union[Unset, 'NetworkInfo'] = UNSET
    hw_encoding_available: Union[Unset, bool] = UNSET
    video_devices: Union[Unset, List['VideoDevice']] = UNSET
    audio_capture_devices: Union[Unset, List['AudioDevice']] = UNSET
    onvif_devices: Union[Unset, List['OnvifDevice']] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        kernel_info: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.kernel_info, Unset):
            kernel_info = self.kernel_info.to_dict()

        os_info: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.os_info, Unset):
            os_info = self.os_info.to_dict()

        node_info: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.node_info, Unset):
            node_info = self.node_info.to_dict()

        network_info: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.network_info, Unset):
            network_info = self.network_info.to_dict()

        hw_encoding_available = self.hw_encoding_available
        video_devices: Union[Unset, List[Dict[str, Any]]] = UNSET
        if not isinstance(self.video_devices, Unset):
            video_devices = []
            for video_devices_item_data in self.video_devices:
                video_devices_item = video_devices_item_data.to_dict()

                video_devices.append(video_devices_item)




        audio_capture_devices: Union[Unset, List[Dict[str, Any]]] = UNSET
        if not isinstance(self.audio_capture_devices, Unset):
            audio_capture_devices = []
            for audio_capture_devices_item_data in self.audio_capture_devices:
                audio_capture_devices_item = audio_capture_devices_item_data.to_dict()

                audio_capture_devices.append(audio_capture_devices_item)




        onvif_devices: Union[Unset, List[Dict[str, Any]]] = UNSET
        if not isinstance(self.onvif_devices, Unset):
            onvif_devices = []
            for onvif_devices_item_data in self.onvif_devices:
                onvif_devices_item = onvif_devices_item_data.to_dict()

                onvif_devices.append(onvif_devices_item)





        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
        })
        if kernel_info is not UNSET:
            field_dict["kernelInfo"] = kernel_info
        if os_info is not UNSET:
            field_dict["osInfo"] = os_info
        if node_info is not UNSET:
            field_dict["nodeInfo"] = node_info
        if network_info is not UNSET:
            field_dict["networkInfo"] = network_info
        if hw_encoding_available is not UNSET:
            field_dict["hwEncodingAvailable"] = hw_encoding_available
        if video_devices is not UNSET:
            field_dict["videoDevices"] = video_devices
        if audio_capture_devices is not UNSET:
            field_dict["audioCaptureDevices"] = audio_capture_devices
        if onvif_devices is not UNSET:
            field_dict["onvifDevices"] = onvif_devices

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.audio_device import AudioDevice
        from ..models.kernel_info import KernelInfo
        from ..models.network_info import NetworkInfo
        from ..models.node_info import NodeInfo
        from ..models.onvif_device import OnvifDevice
        from ..models.os_info import OsInfo
        from ..models.video_device import VideoDevice
        d = src_dict.copy()
        _kernel_info = d.pop("kernelInfo", UNSET)
        kernel_info: Union[Unset, KernelInfo]
        if isinstance(_kernel_info,  Unset):
            kernel_info = UNSET
        else:
            kernel_info = KernelInfo.from_dict(_kernel_info)




        _os_info = d.pop("osInfo", UNSET)
        os_info: Union[Unset, OsInfo]
        if isinstance(_os_info,  Unset):
            os_info = UNSET
        else:
            os_info = OsInfo.from_dict(_os_info)




        _node_info = d.pop("nodeInfo", UNSET)
        node_info: Union[Unset, NodeInfo]
        if isinstance(_node_info,  Unset):
            node_info = UNSET
        else:
            node_info = NodeInfo.from_dict(_node_info)




        _network_info = d.pop("networkInfo", UNSET)
        network_info: Union[Unset, NetworkInfo]
        if isinstance(_network_info,  Unset):
            network_info = UNSET
        else:
            network_info = NetworkInfo.from_dict(_network_info)




        hw_encoding_available = d.pop("hwEncodingAvailable", UNSET)

        video_devices = []
        _video_devices = d.pop("videoDevices", UNSET)
        for video_devices_item_data in (_video_devices or []):
            video_devices_item = VideoDevice.from_dict(video_devices_item_data)



            video_devices.append(video_devices_item)


        audio_capture_devices = []
        _audio_capture_devices = d.pop("audioCaptureDevices", UNSET)
        for audio_capture_devices_item_data in (_audio_capture_devices or []):
            audio_capture_devices_item = AudioDevice.from_dict(audio_capture_devices_item_data)



            audio_capture_devices.append(audio_capture_devices_item)


        onvif_devices = []
        _onvif_devices = d.pop("onvifDevices", UNSET)
        for onvif_devices_item_data in (_onvif_devices or []):
            onvif_devices_item = OnvifDevice.from_dict(onvif_devices_item_data)



            onvif_devices.append(onvif_devices_item)


        hw_info = cls(
            kernel_info=kernel_info,
            os_info=os_info,
            node_info=node_info,
            network_info=network_info,
            hw_encoding_available=hw_encoding_available,
            video_devices=video_devices,
            audio_capture_devices=audio_capture_devices,
            onvif_devices=onvif_devices,
        )

        hw_info.additional_properties = d
        return hw_info

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
