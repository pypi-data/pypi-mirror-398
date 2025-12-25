from typing import Any, Dict, List, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

T = TypeVar("T", bound="NodeInfo")

@attr.s(auto_attribs=True)
class NodeInfo:
    """
    Attributes:
        hostname (Union[Unset, str]):
        machineid (Union[Unset, str]):
        timezone (Union[Unset, str]):
    """

    hostname: Union[Unset, str] = UNSET
    machineid: Union[Unset, str] = UNSET
    timezone: Union[Unset, str] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        hostname = self.hostname
        machineid = self.machineid
        timezone = self.timezone

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
        })
        if hostname is not UNSET:
            field_dict["hostname"] = hostname
        if machineid is not UNSET:
            field_dict["machineid"] = machineid
        if timezone is not UNSET:
            field_dict["timezone"] = timezone

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        hostname = d.pop("hostname", UNSET)

        machineid = d.pop("machineid", UNSET)

        timezone = d.pop("timezone", UNSET)

        node_info = cls(
            hostname=hostname,
            machineid=machineid,
            timezone=timezone,
        )

        node_info.additional_properties = d
        return node_info

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
