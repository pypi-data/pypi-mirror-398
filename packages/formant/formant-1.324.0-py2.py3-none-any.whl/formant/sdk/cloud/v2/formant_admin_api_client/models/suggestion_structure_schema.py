from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar

import attr

if TYPE_CHECKING:
  from ..models.suggestion_structure_object_schema import \
      SuggestionStructureObjectSchema




T = TypeVar("T", bound="SuggestionStructureSchema")

@attr.s(auto_attribs=True)
class SuggestionStructureSchema:
    """
    Attributes:
        name (str):
        description (str):
        parameters (SuggestionStructureObjectSchema):
    """

    name: str
    description: str
    parameters: 'SuggestionStructureObjectSchema'
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        name = self.name
        description = self.description
        parameters = self.parameters.to_dict()


        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "name": name,
            "description": description,
            "parameters": parameters,
        })

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.suggestion_structure_object_schema import \
            SuggestionStructureObjectSchema
        d = src_dict.copy()
        name = d.pop("name")

        description = d.pop("description")

        parameters = SuggestionStructureObjectSchema.from_dict(d.pop("parameters"))




        suggestion_structure_schema = cls(
            name=name,
            description=description,
            parameters=parameters,
        )

        suggestion_structure_schema.additional_properties = d
        return suggestion_structure_schema

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
