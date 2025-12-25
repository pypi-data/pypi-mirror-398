from typing import Any, Dict, List, Type, TypeVar

import attr

from ..models.challenge_type import ChallengeType

T = TypeVar("T", bound="Challenge")

@attr.s(auto_attribs=True)
class Challenge:
    """
    Attributes:
        type (ChallengeType):
        session (str):
        user_id (str):
        email (str):
    """

    type: ChallengeType
    session: str
    user_id: str
    email: str
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        type = self.type.value

        session = self.session
        user_id = self.user_id
        email = self.email

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "type": type,
            "session": session,
            "userId": user_id,
            "email": email,
        })

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        type = ChallengeType(d.pop("type"))




        session = d.pop("session")

        user_id = d.pop("userId")

        email = d.pop("email")

        challenge = cls(
            type=type,
            session=session,
            user_id=user_id,
            email=email,
        )

        challenge.additional_properties = d
        return challenge

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
