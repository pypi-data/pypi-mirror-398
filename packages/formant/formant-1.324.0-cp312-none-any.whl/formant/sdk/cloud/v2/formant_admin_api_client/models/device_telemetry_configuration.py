from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

if TYPE_CHECKING:
  from ..models.device_ros_configuration import DeviceRosConfiguration
  from ..models.device_stream_configuration import DeviceStreamConfiguration




T = TypeVar("T", bound="DeviceTelemetryConfiguration")

@attr.s(auto_attribs=True)
class DeviceTelemetryConfiguration:
    """
    Attributes:
        streams (Union[Unset, List['DeviceStreamConfiguration']]):
        ros (Union[Unset, DeviceRosConfiguration]):
    """

    streams: Union[Unset, List['DeviceStreamConfiguration']] = UNSET
    ros: Union[Unset, 'DeviceRosConfiguration'] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        streams: Union[Unset, List[Dict[str, Any]]] = UNSET
        if not isinstance(self.streams, Unset):
            streams = []
            for streams_item_data in self.streams:
                streams_item = streams_item_data.to_dict()

                streams.append(streams_item)




        ros: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.ros, Unset):
            ros = self.ros.to_dict()


        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
        })
        if streams is not UNSET:
            field_dict["streams"] = streams
        if ros is not UNSET:
            field_dict["ros"] = ros

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.device_ros_configuration import DeviceRosConfiguration
        from ..models.device_stream_configuration import \
            DeviceStreamConfiguration
        d = src_dict.copy()
        streams = []
        _streams = d.pop("streams", UNSET)
        for streams_item_data in (_streams or []):
            streams_item = DeviceStreamConfiguration.from_dict(streams_item_data)



            streams.append(streams_item)


        _ros = d.pop("ros", UNSET)
        ros: Union[Unset, DeviceRosConfiguration]
        if isinstance(_ros,  Unset):
            ros = UNSET
        else:
            ros = DeviceRosConfiguration.from_dict(_ros)




        device_telemetry_configuration = cls(
            streams=streams,
            ros=ros,
        )

        device_telemetry_configuration.additional_properties = d
        return device_telemetry_configuration

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
