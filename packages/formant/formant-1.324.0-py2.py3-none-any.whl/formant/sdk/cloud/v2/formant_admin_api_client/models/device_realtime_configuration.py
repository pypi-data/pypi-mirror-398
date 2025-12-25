from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

if TYPE_CHECKING:
  from ..models.device_teleop_custom_stream_configuration import \
      DeviceTeleopCustomStreamConfiguration
  from ..models.device_teleop_hardware_stream_configuration import \
      DeviceTeleopHardwareStreamConfiguration
  from ..models.device_teleop_ros_stream_configuration import \
      DeviceTeleopRosStreamConfiguration




T = TypeVar("T", bound="DeviceRealtimeConfiguration")

@attr.s(auto_attribs=True)
class DeviceRealtimeConfiguration:
    """
    Attributes:
        ros_streams (Union[Unset, List['DeviceTeleopRosStreamConfiguration']]):
        custom_streams (Union[Unset, List['DeviceTeleopCustomStreamConfiguration']]):
        hardware_streams (Union[Unset, List['DeviceTeleopHardwareStreamConfiguration']]):
    """

    ros_streams: Union[Unset, List['DeviceTeleopRosStreamConfiguration']] = UNSET
    custom_streams: Union[Unset, List['DeviceTeleopCustomStreamConfiguration']] = UNSET
    hardware_streams: Union[Unset, List['DeviceTeleopHardwareStreamConfiguration']] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        ros_streams: Union[Unset, List[Dict[str, Any]]] = UNSET
        if not isinstance(self.ros_streams, Unset):
            ros_streams = []
            for ros_streams_item_data in self.ros_streams:
                ros_streams_item = ros_streams_item_data.to_dict()

                ros_streams.append(ros_streams_item)




        custom_streams: Union[Unset, List[Dict[str, Any]]] = UNSET
        if not isinstance(self.custom_streams, Unset):
            custom_streams = []
            for custom_streams_item_data in self.custom_streams:
                custom_streams_item = custom_streams_item_data.to_dict()

                custom_streams.append(custom_streams_item)




        hardware_streams: Union[Unset, List[Dict[str, Any]]] = UNSET
        if not isinstance(self.hardware_streams, Unset):
            hardware_streams = []
            for hardware_streams_item_data in self.hardware_streams:
                hardware_streams_item = hardware_streams_item_data.to_dict()

                hardware_streams.append(hardware_streams_item)





        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
        })
        if ros_streams is not UNSET:
            field_dict["rosStreams"] = ros_streams
        if custom_streams is not UNSET:
            field_dict["customStreams"] = custom_streams
        if hardware_streams is not UNSET:
            field_dict["hardwareStreams"] = hardware_streams

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.device_teleop_custom_stream_configuration import \
            DeviceTeleopCustomStreamConfiguration
        from ..models.device_teleop_hardware_stream_configuration import \
            DeviceTeleopHardwareStreamConfiguration
        from ..models.device_teleop_ros_stream_configuration import \
            DeviceTeleopRosStreamConfiguration
        d = src_dict.copy()
        ros_streams = []
        _ros_streams = d.pop("rosStreams", UNSET)
        for ros_streams_item_data in (_ros_streams or []):
            ros_streams_item = DeviceTeleopRosStreamConfiguration.from_dict(ros_streams_item_data)



            ros_streams.append(ros_streams_item)


        custom_streams = []
        _custom_streams = d.pop("customStreams", UNSET)
        for custom_streams_item_data in (_custom_streams or []):
            custom_streams_item = DeviceTeleopCustomStreamConfiguration.from_dict(custom_streams_item_data)



            custom_streams.append(custom_streams_item)


        hardware_streams = []
        _hardware_streams = d.pop("hardwareStreams", UNSET)
        for hardware_streams_item_data in (_hardware_streams or []):
            hardware_streams_item = DeviceTeleopHardwareStreamConfiguration.from_dict(hardware_streams_item_data)



            hardware_streams.append(hardware_streams_item)


        device_realtime_configuration = cls(
            ros_streams=ros_streams,
            custom_streams=custom_streams,
            hardware_streams=hardware_streams,
        )

        device_realtime_configuration.additional_properties = d
        return device_realtime_configuration

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
