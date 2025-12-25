from typing import Any, Dict, List, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

T = TypeVar("T", bound="OsInfo")

@attr.s(auto_attribs=True)
class OsInfo:
    """
    Attributes:
        name (Union[Unset, str]):
        vendor (Union[Unset, str]):
        release (Union[Unset, str]):
        version (Union[Unset, str]):
    """

    name: Union[Unset, str] = UNSET
    vendor: Union[Unset, str] = UNSET
    release: Union[Unset, str] = UNSET
    version: Union[Unset, str] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        name = self.name
        vendor = self.vendor
        release = self.release
        version = self.version

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
        })
        if name is not UNSET:
            field_dict["name"] = name
        if vendor is not UNSET:
            field_dict["vendor"] = vendor
        if release is not UNSET:
            field_dict["release"] = release
        if version is not UNSET:
            field_dict["version"] = version

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        name = d.pop("name", UNSET)

        vendor = d.pop("vendor", UNSET)

        release = d.pop("release", UNSET)

        version = d.pop("version", UNSET)

        os_info = cls(
            name=name,
            vendor=vendor,
            release=release,
            version=version,
        )

        os_info.additional_properties = d
        return os_info

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
