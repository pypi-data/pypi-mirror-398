from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union, cast

import attr

from ..types import UNSET, Unset

if TYPE_CHECKING:
  from ..models.suggestion_structure_schema import SuggestionStructureSchema




T = TypeVar("T", bound="ThinkingRequest")

@attr.s(auto_attribs=True)
class ThinkingRequest:
    """
    Attributes:
        actions (List['SuggestionStructureSchema']):
        prompt (str):
        facts (Union[Unset, List[str]]):
        principles (Union[Unset, List[str]]):
        goals (Union[Unset, List[str]]):
        model (Union[Unset, str]):
    """

    actions: List['SuggestionStructureSchema']
    prompt: str
    facts: Union[Unset, List[str]] = UNSET
    principles: Union[Unset, List[str]] = UNSET
    goals: Union[Unset, List[str]] = UNSET
    model: Union[Unset, str] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        actions = []
        for actions_item_data in self.actions:
            actions_item = actions_item_data.to_dict()

            actions.append(actions_item)




        prompt = self.prompt
        facts: Union[Unset, List[str]] = UNSET
        if not isinstance(self.facts, Unset):
            facts = self.facts




        principles: Union[Unset, List[str]] = UNSET
        if not isinstance(self.principles, Unset):
            principles = self.principles




        goals: Union[Unset, List[str]] = UNSET
        if not isinstance(self.goals, Unset):
            goals = self.goals




        model = self.model

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "actions": actions,
            "prompt": prompt,
        })
        if facts is not UNSET:
            field_dict["facts"] = facts
        if principles is not UNSET:
            field_dict["principles"] = principles
        if goals is not UNSET:
            field_dict["goals"] = goals
        if model is not UNSET:
            field_dict["model"] = model

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.suggestion_structure_schema import \
            SuggestionStructureSchema
        d = src_dict.copy()
        actions = []
        _actions = d.pop("actions")
        for actions_item_data in (_actions):
            actions_item = SuggestionStructureSchema.from_dict(actions_item_data)



            actions.append(actions_item)


        prompt = d.pop("prompt")

        facts = cast(List[str], d.pop("facts", UNSET))


        principles = cast(List[str], d.pop("principles", UNSET))


        goals = cast(List[str], d.pop("goals", UNSET))


        model = d.pop("model", UNSET)

        thinking_request = cls(
            actions=actions,
            prompt=prompt,
            facts=facts,
            principles=principles,
            goals=goals,
            model=model,
        )

        thinking_request.additional_properties = d
        return thinking_request

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
