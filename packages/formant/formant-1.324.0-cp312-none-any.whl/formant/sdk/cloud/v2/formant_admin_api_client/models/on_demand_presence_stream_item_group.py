from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar

import attr

from ..models.on_demand_presence_stream_item_group_datapoint_type import \
    OnDemandPresenceStreamItemGroupDatapointType

if TYPE_CHECKING:
  from ..models.on_demand_presence_time_range import OnDemandPresenceTimeRange




T = TypeVar("T", bound="OnDemandPresenceStreamItemGroup")

@attr.s(auto_attribs=True)
class OnDemandPresenceStreamItemGroup:
    """
    Attributes:
        datapoint_type (OnDemandPresenceStreamItemGroupDatapointType):
        time_ranges (List['OnDemandPresenceTimeRange']):
    """

    datapoint_type: OnDemandPresenceStreamItemGroupDatapointType
    time_ranges: List['OnDemandPresenceTimeRange']
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        datapoint_type = self.datapoint_type.value

        time_ranges = []
        for time_ranges_item_data in self.time_ranges:
            time_ranges_item = time_ranges_item_data.to_dict()

            time_ranges.append(time_ranges_item)





        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "datapointType": datapoint_type,
            "timeRanges": time_ranges,
        })

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.on_demand_presence_time_range import \
            OnDemandPresenceTimeRange
        d = src_dict.copy()
        datapoint_type = OnDemandPresenceStreamItemGroupDatapointType(d.pop("datapointType"))




        time_ranges = []
        _time_ranges = d.pop("timeRanges")
        for time_ranges_item_data in (_time_ranges):
            time_ranges_item = OnDemandPresenceTimeRange.from_dict(time_ranges_item_data)



            time_ranges.append(time_ranges_item)


        on_demand_presence_stream_item_group = cls(
            datapoint_type=datapoint_type,
            time_ranges=time_ranges,
        )

        on_demand_presence_stream_item_group.additional_properties = d
        return on_demand_presence_stream_item_group

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
