from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar

import attr

if TYPE_CHECKING:
  from ..models.network import Network




T = TypeVar("T", bound="NetworkInfo")

@attr.s(auto_attribs=True)
class NetworkInfo:
    """
    Attributes:
        networks (List['Network']):
    """

    networks: List['Network']
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        networks = []
        for networks_item_data in self.networks:
            networks_item = networks_item_data.to_dict()

            networks.append(networks_item)





        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "networks": networks,
        })

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.network import Network
        d = src_dict.copy()
        networks = []
        _networks = d.pop("networks")
        for networks_item_data in (_networks):
            networks_item = Network.from_dict(networks_item_data)



            networks.append(networks_item)


        network_info = cls(
            networks=networks,
        )

        network_info.additional_properties = d
        return network_info

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
