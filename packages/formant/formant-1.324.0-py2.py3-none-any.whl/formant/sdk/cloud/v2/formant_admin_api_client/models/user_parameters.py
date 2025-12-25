from typing import Any, Dict, List, Type, TypeVar, Union

import attr

from ..models.user_parameters_roles_item import UserParametersRolesItem
from ..types import UNSET, Unset

T = TypeVar("T", bound="UserParameters")

@attr.s(auto_attribs=True)
class UserParameters:
    """
    Attributes:
        roles (Union[Unset, List[UserParametersRolesItem]]):
    """

    roles: Union[Unset, List[UserParametersRolesItem]] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        roles: Union[Unset, List[str]] = UNSET
        if not isinstance(self.roles, Unset):
            roles = []
            for roles_item_data in self.roles:
                roles_item = roles_item_data.value

                roles.append(roles_item)





        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
        })
        if roles is not UNSET:
            field_dict["roles"] = roles

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        roles = []
        _roles = d.pop("roles", UNSET)
        for roles_item_data in (_roles or []):
            roles_item = UserParametersRolesItem(roles_item_data)



            roles.append(roles_item)


        user_parameters = cls(
            roles=roles,
        )

        user_parameters.additional_properties = d
        return user_parameters

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
