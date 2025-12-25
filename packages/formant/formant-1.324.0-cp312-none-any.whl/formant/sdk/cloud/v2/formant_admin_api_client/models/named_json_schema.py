from typing import Any, Dict, List, Type, TypeVar

import attr

from ..models.named_json_schema_schema_type import NamedJsonSchemaSchemaType

T = TypeVar("T", bound="NamedJsonSchema")

@attr.s(auto_attribs=True)
class NamedJsonSchema:
    """
    Attributes:
        name (str):
        id (str):
        url (str):
        schema_type (NamedJsonSchemaSchemaType):
    """

    name: str
    id: str
    url: str
    schema_type: NamedJsonSchemaSchemaType
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        name = self.name
        id = self.id
        url = self.url
        schema_type = self.schema_type.value


        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "name": name,
            "id": id,
            "url": url,
            "schemaType": schema_type,
        })

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        name = d.pop("name")

        id = d.pop("id")

        url = d.pop("url")

        schema_type = NamedJsonSchemaSchemaType(d.pop("schemaType"))




        named_json_schema = cls(
            name=name,
            id=id,
            url=url,
            schema_type=schema_type,
        )

        named_json_schema.additional_properties = d
        return named_json_schema

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
