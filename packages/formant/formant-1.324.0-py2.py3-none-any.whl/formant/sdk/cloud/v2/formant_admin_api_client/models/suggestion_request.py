from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

if TYPE_CHECKING:
  from ..models.application_context import ApplicationContext
  from ..models.suggestion_structure_schema import SuggestionStructureSchema




T = TypeVar("T", bound="SuggestionRequest")

@attr.s(auto_attribs=True)
class SuggestionRequest:
    """
    Attributes:
        prompt (str):
        structures (List['SuggestionStructureSchema']):
        model (Union[Unset, str]):
        system_context (Union[Unset, ApplicationContext]):
    """

    prompt: str
    structures: List['SuggestionStructureSchema']
    model: Union[Unset, str] = UNSET
    system_context: Union[Unset, 'ApplicationContext'] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        prompt = self.prompt
        structures = []
        for structures_item_data in self.structures:
            structures_item = structures_item_data.to_dict()

            structures.append(structures_item)




        model = self.model
        system_context: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.system_context, Unset):
            system_context = self.system_context.to_dict()


        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "prompt": prompt,
            "structures": structures,
        })
        if model is not UNSET:
            field_dict["model"] = model
        if system_context is not UNSET:
            field_dict["systemContext"] = system_context

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.application_context import ApplicationContext
        from ..models.suggestion_structure_schema import \
            SuggestionStructureSchema
        d = src_dict.copy()
        prompt = d.pop("prompt")

        structures = []
        _structures = d.pop("structures")
        for structures_item_data in (_structures):
            structures_item = SuggestionStructureSchema.from_dict(structures_item_data)



            structures.append(structures_item)


        model = d.pop("model", UNSET)

        _system_context = d.pop("systemContext", UNSET)
        system_context: Union[Unset, ApplicationContext]
        if isinstance(_system_context,  Unset):
            system_context = UNSET
        else:
            system_context = ApplicationContext.from_dict(_system_context)




        suggestion_request = cls(
            prompt=prompt,
            structures=structures,
            model=model,
            system_context=system_context,
        )

        suggestion_request.additional_properties = d
        return suggestion_request

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
