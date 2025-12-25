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
  from ..models.teleop_joystick_configuration import \
      TeleopJoystickConfiguration
  from ..models.teleop_view_configuration import TeleopViewConfiguration




T = TypeVar("T", bound="DeviceTeleopConfiguration")

@attr.s(auto_attribs=True)
class DeviceTeleopConfiguration:
    """
    Attributes:
        ros_streams (Union[Unset, List['DeviceTeleopRosStreamConfiguration']]):
        custom_streams (Union[Unset, List['DeviceTeleopCustomStreamConfiguration']]):
        hardware_streams (Union[Unset, List['DeviceTeleopHardwareStreamConfiguration']]):
        joysticks (Union[Unset, TeleopJoystickConfiguration]):
        views (Union[Unset, TeleopViewConfiguration]):
        arm_switch (Union[Unset, bool]):
        allow_low_bandwidth_mode (Union[Unset, bool]):
        disable_high_ping_warning (Union[Unset, bool]):
    """

    ros_streams: Union[Unset, List['DeviceTeleopRosStreamConfiguration']] = UNSET
    custom_streams: Union[Unset, List['DeviceTeleopCustomStreamConfiguration']] = UNSET
    hardware_streams: Union[Unset, List['DeviceTeleopHardwareStreamConfiguration']] = UNSET
    joysticks: Union[Unset, 'TeleopJoystickConfiguration'] = UNSET
    views: Union[Unset, 'TeleopViewConfiguration'] = UNSET
    arm_switch: Union[Unset, bool] = UNSET
    allow_low_bandwidth_mode: Union[Unset, bool] = UNSET
    disable_high_ping_warning: Union[Unset, bool] = UNSET
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




        joysticks: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.joysticks, Unset):
            joysticks = self.joysticks.to_dict()

        views: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.views, Unset):
            views = self.views.to_dict()

        arm_switch = self.arm_switch
        allow_low_bandwidth_mode = self.allow_low_bandwidth_mode
        disable_high_ping_warning = self.disable_high_ping_warning

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
        if joysticks is not UNSET:
            field_dict["joysticks"] = joysticks
        if views is not UNSET:
            field_dict["views"] = views
        if arm_switch is not UNSET:
            field_dict["armSwitch"] = arm_switch
        if allow_low_bandwidth_mode is not UNSET:
            field_dict["allowLowBandwidthMode"] = allow_low_bandwidth_mode
        if disable_high_ping_warning is not UNSET:
            field_dict["disableHighPingWarning"] = disable_high_ping_warning

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.device_teleop_custom_stream_configuration import \
            DeviceTeleopCustomStreamConfiguration
        from ..models.device_teleop_hardware_stream_configuration import \
            DeviceTeleopHardwareStreamConfiguration
        from ..models.device_teleop_ros_stream_configuration import \
            DeviceTeleopRosStreamConfiguration
        from ..models.teleop_joystick_configuration import \
            TeleopJoystickConfiguration
        from ..models.teleop_view_configuration import TeleopViewConfiguration
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


        _joysticks = d.pop("joysticks", UNSET)
        joysticks: Union[Unset, TeleopJoystickConfiguration]
        if isinstance(_joysticks,  Unset):
            joysticks = UNSET
        else:
            joysticks = TeleopJoystickConfiguration.from_dict(_joysticks)




        _views = d.pop("views", UNSET)
        views: Union[Unset, TeleopViewConfiguration]
        if isinstance(_views,  Unset):
            views = UNSET
        else:
            views = TeleopViewConfiguration.from_dict(_views)




        arm_switch = d.pop("armSwitch", UNSET)

        allow_low_bandwidth_mode = d.pop("allowLowBandwidthMode", UNSET)

        disable_high_ping_warning = d.pop("disableHighPingWarning", UNSET)

        device_teleop_configuration = cls(
            ros_streams=ros_streams,
            custom_streams=custom_streams,
            hardware_streams=hardware_streams,
            joysticks=joysticks,
            views=views,
            arm_switch=arm_switch,
            allow_low_bandwidth_mode=allow_low_bandwidth_mode,
            disable_high_ping_warning=disable_high_ping_warning,
        )

        device_teleop_configuration.additional_properties = d
        return device_teleop_configuration

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
