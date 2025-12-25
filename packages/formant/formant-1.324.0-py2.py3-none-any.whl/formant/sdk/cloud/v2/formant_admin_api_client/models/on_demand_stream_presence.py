from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar

import attr

if TYPE_CHECKING:
  from ..models.on_demand_presence_stream_item_group import \
      OnDemandPresenceStreamItemGroup




T = TypeVar("T", bound="OnDemandStreamPresence")

@attr.s(auto_attribs=True)
class OnDemandStreamPresence:
    """
    Attributes:
        stream_name (str):
        presence (List['OnDemandPresenceStreamItemGroup']):
    """

    stream_name: str
    presence: List['OnDemandPresenceStreamItemGroup']
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        stream_name = self.stream_name
        presence = []
        for presence_item_data in self.presence:
            presence_item = presence_item_data.to_dict()

            presence.append(presence_item)





        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "streamName": stream_name,
            "presence": presence,
        })

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.on_demand_presence_stream_item_group import \
            OnDemandPresenceStreamItemGroup
        d = src_dict.copy()
        stream_name = d.pop("streamName")

        presence = []
        _presence = d.pop("presence")
        for presence_item_data in (_presence):
            presence_item = OnDemandPresenceStreamItemGroup.from_dict(presence_item_data)



            presence.append(presence_item)


        on_demand_stream_presence = cls(
            stream_name=stream_name,
            presence=presence,
        )

        on_demand_stream_presence.additional_properties = d
        return on_demand_stream_presence

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
