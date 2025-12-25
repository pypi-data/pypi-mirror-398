from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar

import attr

from ..models.on_demand_buffer_buffer_type import OnDemandBufferBufferType

if TYPE_CHECKING:
  from ..models.on_demand_stream_presence import OnDemandStreamPresence




T = TypeVar("T", bound="OnDemandBuffer")

@attr.s(auto_attribs=True)
class OnDemandBuffer:
    """
    Attributes:
        buffer_type (OnDemandBufferBufferType):
        streams (List['OnDemandStreamPresence']):
    """

    buffer_type: OnDemandBufferBufferType
    streams: List['OnDemandStreamPresence']
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        buffer_type = self.buffer_type.value

        streams = []
        for streams_item_data in self.streams:
            streams_item = streams_item_data.to_dict()

            streams.append(streams_item)





        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "bufferType": buffer_type,
            "streams": streams,
        })

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.on_demand_stream_presence import OnDemandStreamPresence
        d = src_dict.copy()
        buffer_type = OnDemandBufferBufferType(d.pop("bufferType"))




        streams = []
        _streams = d.pop("streams")
        for streams_item_data in (_streams):
            streams_item = OnDemandStreamPresence.from_dict(streams_item_data)



            streams.append(streams_item)


        on_demand_buffer = cls(
            buffer_type=buffer_type,
            streams=streams,
        )

        on_demand_buffer.additional_properties = d
        return on_demand_buffer

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
