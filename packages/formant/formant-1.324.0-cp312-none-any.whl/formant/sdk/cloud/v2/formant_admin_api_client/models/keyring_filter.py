from typing import Any, Dict, List, Type, TypeVar, Union, cast

import attr

from ..models.keyring_filter_auth_type import KeyringFilterAuthType
from ..types import UNSET, Unset

T = TypeVar("T", bound="KeyringFilter")

@attr.s(auto_attribs=True)
class KeyringFilter:
    """
    Attributes:
        integration_ids (Union[Unset, List[str]]):
        auth_type (Union[Unset, KeyringFilterAuthType]):
    """

    integration_ids: Union[Unset, List[str]] = UNSET
    auth_type: Union[Unset, KeyringFilterAuthType] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        integration_ids: Union[Unset, List[str]] = UNSET
        if not isinstance(self.integration_ids, Unset):
            integration_ids = self.integration_ids




        auth_type: Union[Unset, str] = UNSET
        if not isinstance(self.auth_type, Unset):
            auth_type = self.auth_type.value


        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
        })
        if integration_ids is not UNSET:
            field_dict["integrationIds"] = integration_ids
        if auth_type is not UNSET:
            field_dict["authType"] = auth_type

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        integration_ids = cast(List[str], d.pop("integrationIds", UNSET))


        _auth_type = d.pop("authType", UNSET)
        auth_type: Union[Unset, KeyringFilterAuthType]
        if isinstance(_auth_type,  Unset):
            auth_type = UNSET
        else:
            auth_type = KeyringFilterAuthType(_auth_type)




        keyring_filter = cls(
            integration_ids=integration_ids,
            auth_type=auth_type,
        )

        keyring_filter.additional_properties = d
        return keyring_filter

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
