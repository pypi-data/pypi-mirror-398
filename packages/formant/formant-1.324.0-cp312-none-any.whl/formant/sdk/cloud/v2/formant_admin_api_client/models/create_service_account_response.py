from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar

import attr

if TYPE_CHECKING:
  from ..models.user import User




T = TypeVar("T", bound="CreateServiceAccountResponse")

@attr.s(auto_attribs=True)
class CreateServiceAccountResponse:
    """
    Attributes:
        user (User):
        password (str):
    """

    user: 'User'
    password: str
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        user = self.user.to_dict()

        password = self.password

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "user": user,
            "password": password,
        })

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.user import User
        d = src_dict.copy()
        user = User.from_dict(d.pop("user"))




        password = d.pop("password")

        create_service_account_response = cls(
            user=user,
            password=password,
        )

        create_service_account_response.additional_properties = d
        return create_service_account_response

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
