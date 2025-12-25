from typing import Any, Dict, List, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

T = TypeVar("T", bound="TeleopViewConfiguration")

@attr.s(auto_attribs=True)
class TeleopViewConfiguration:
    """
    Attributes:
        stream_name (Union[Unset, Any]):
        configuration_id (Union[Unset, Any]):
    """

    stream_name: Union[Unset, Any] = UNSET
    configuration_id: Union[Unset, Any] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        stream_name = self.stream_name
        configuration_id = self.configuration_id

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
        })
        if stream_name is not UNSET:
            field_dict["streamName"] = stream_name
        if configuration_id is not UNSET:
            field_dict["configurationId"] = configuration_id

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        stream_name = d.pop("streamName", UNSET)

        configuration_id = d.pop("configurationId", UNSET)

        teleop_view_configuration = cls(
            stream_name=stream_name,
            configuration_id=configuration_id,
        )

        teleop_view_configuration.additional_properties = d
        return teleop_view_configuration

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
