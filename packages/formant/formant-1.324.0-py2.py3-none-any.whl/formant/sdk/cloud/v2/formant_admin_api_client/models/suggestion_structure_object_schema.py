from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union, cast

import attr

from ..types import UNSET, Unset

if TYPE_CHECKING:
  from ..models.suggestion_structure_object_schema_properties import \
      SuggestionStructureObjectSchemaProperties




T = TypeVar("T", bound="SuggestionStructureObjectSchema")

@attr.s(auto_attribs=True)
class SuggestionStructureObjectSchema:
    """
    Attributes:
        type (str):
        properties (SuggestionStructureObjectSchemaProperties):
        required (Union[Unset, List[str]]):
    """

    type: str
    properties: 'SuggestionStructureObjectSchemaProperties'
    required: Union[Unset, List[str]] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        type = self.type
        properties = self.properties.to_dict()

        required: Union[Unset, List[str]] = UNSET
        if not isinstance(self.required, Unset):
            required = self.required





        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "type": type,
            "properties": properties,
        })
        if required is not UNSET:
            field_dict["required"] = required

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.suggestion_structure_object_schema_properties import \
            SuggestionStructureObjectSchemaProperties
        d = src_dict.copy()
        type = d.pop("type")

        properties = SuggestionStructureObjectSchemaProperties.from_dict(d.pop("properties"))




        required = cast(List[str], d.pop("required", UNSET))


        suggestion_structure_object_schema = cls(
            type=type,
            properties=properties,
            required=required,
        )

        suggestion_structure_object_schema.additional_properties = d
        return suggestion_structure_object_schema

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
