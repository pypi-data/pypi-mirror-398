from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar

import attr

if TYPE_CHECKING:
  from ..models.on_demand_buffer import OnDemandBuffer




T = TypeVar("T", bound="OnDemandState")

@attr.s(auto_attribs=True)
class OnDemandState:
    """
    Attributes:
        buffers (List['OnDemandBuffer']):
    """

    buffers: List['OnDemandBuffer']
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        buffers = []
        for buffers_item_data in self.buffers:
            buffers_item = buffers_item_data.to_dict()

            buffers.append(buffers_item)





        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "buffers": buffers,
        })

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.on_demand_buffer import OnDemandBuffer
        d = src_dict.copy()
        buffers = []
        _buffers = d.pop("buffers")
        for buffers_item_data in (_buffers):
            buffers_item = OnDemandBuffer.from_dict(buffers_item_data)



            buffers.append(buffers_item)


        on_demand_state = cls(
            buffers=buffers,
        )

        on_demand_state.additional_properties = d
        return on_demand_state

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
