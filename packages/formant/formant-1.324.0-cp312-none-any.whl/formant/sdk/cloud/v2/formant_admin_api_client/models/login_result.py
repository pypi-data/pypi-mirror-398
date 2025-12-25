from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

if TYPE_CHECKING:
  from ..models.authentication import Authentication
  from ..models.challenge import Challenge




T = TypeVar("T", bound="LoginResult")

@attr.s(auto_attribs=True)
class LoginResult:
    """
    Attributes:
        authentication (Authentication):
        challenge (Union[Unset, Challenge]):
        is_existing_user (Union[Unset, bool]):
    """

    authentication: 'Authentication'
    challenge: Union[Unset, 'Challenge'] = UNSET
    is_existing_user: Union[Unset, bool] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        authentication = self.authentication.to_dict()

        challenge: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.challenge, Unset):
            challenge = self.challenge.to_dict()

        is_existing_user = self.is_existing_user

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "authentication": authentication,
        })
        if challenge is not UNSET:
            field_dict["challenge"] = challenge
        if is_existing_user is not UNSET:
            field_dict["isExistingUser"] = is_existing_user

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.authentication import Authentication
        from ..models.challenge import Challenge
        d = src_dict.copy()
        authentication = Authentication.from_dict(d.pop("authentication"))




        _challenge = d.pop("challenge", UNSET)
        challenge: Union[Unset, Challenge]
        if isinstance(_challenge,  Unset):
            challenge = UNSET
        else:
            challenge = Challenge.from_dict(_challenge)




        is_existing_user = d.pop("isExistingUser", UNSET)

        login_result = cls(
            authentication=authentication,
            challenge=challenge,
            is_existing_user=is_existing_user,
        )

        login_result.additional_properties = d
        return login_result

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
