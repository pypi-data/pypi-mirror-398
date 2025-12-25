from typing import Any, Dict, List, Type, TypeVar

import attr

T = TypeVar("T", bound="ValidationConfiguration")

@attr.s(auto_attribs=True)
class ValidationConfiguration:
    """
    Attributes:
        schema_id (str):
    """

    schema_id: str
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        schema_id = self.schema_id

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "schemaId": schema_id,
        })

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        schema_id = d.pop("schemaId")

        validation_configuration = cls(
            schema_id=schema_id,
        )

        validation_configuration.additional_properties = d
        return validation_configuration

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
