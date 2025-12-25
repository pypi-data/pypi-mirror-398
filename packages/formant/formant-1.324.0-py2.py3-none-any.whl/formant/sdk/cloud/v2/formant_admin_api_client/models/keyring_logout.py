from typing import Any, Dict, List, Type, TypeVar, Union, cast

import attr

from ..types import UNSET, Unset

T = TypeVar("T", bound="KeyringLogout")

@attr.s(auto_attribs=True)
class KeyringLogout:
    """
    Attributes:
        integration_ids (Union[Unset, List[str]]):
    """

    integration_ids: Union[Unset, List[str]] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        integration_ids: Union[Unset, List[str]] = UNSET
        if not isinstance(self.integration_ids, Unset):
            integration_ids = self.integration_ids





        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
        })
        if integration_ids is not UNSET:
            field_dict["integrationIds"] = integration_ids

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        integration_ids = cast(List[str], d.pop("integrationIds", UNSET))


        keyring_logout = cls(
            integration_ids=integration_ids,
        )

        keyring_logout.additional_properties = d
        return keyring_logout

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
