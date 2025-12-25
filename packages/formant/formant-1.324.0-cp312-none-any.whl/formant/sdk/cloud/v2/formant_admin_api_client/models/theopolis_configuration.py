from typing import Any, Dict, List, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

T = TypeVar("T", bound="TheopolisConfiguration")

@attr.s(auto_attribs=True)
class TheopolisConfiguration:
    """
    Attributes:
        user_id (str):
        persona_id (str):
        description (str):
        goal (str):
        model (Union[Unset, str]):
    """

    user_id: str
    persona_id: str
    description: str
    goal: str
    model: Union[Unset, str] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        user_id = self.user_id
        persona_id = self.persona_id
        description = self.description
        goal = self.goal
        model = self.model

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "userId": user_id,
            "personaId": persona_id,
            "description": description,
            "goal": goal,
        })
        if model is not UNSET:
            field_dict["model"] = model

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        user_id = d.pop("userId")

        persona_id = d.pop("personaId")

        description = d.pop("description")

        goal = d.pop("goal")

        model = d.pop("model", UNSET)

        theopolis_configuration = cls(
            user_id=user_id,
            persona_id=persona_id,
            description=description,
            goal=goal,
            model=model,
        )

        theopolis_configuration.additional_properties = d
        return theopolis_configuration

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
