from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union

import attr

from ..models.annotation_field_type import AnnotationFieldType
from ..types import UNSET, Unset

if TYPE_CHECKING:
  from ..models.sheet_parameters import SheetParameters
  from ..models.tag_parameters import TagParameters
  from ..models.user_parameters import UserParameters




T = TypeVar("T", bound="AnnotationField")

@attr.s(auto_attribs=True)
class AnnotationField:
    """
    Attributes:
        type (AnnotationFieldType):
        key (Any):
        name (str):
        required (bool):
        parameters (Union['SheetParameters', 'TagParameters', 'UserParameters']):
        description (Union[Unset, str]):
    """

    type: AnnotationFieldType
    key: Any
    name: str
    required: bool
    parameters: Union['SheetParameters', 'TagParameters', 'UserParameters']
    description: Union[Unset, str] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        from ..models.tag_parameters import TagParameters
        from ..models.user_parameters import UserParameters
        type = self.type.value

        key = self.key
        name = self.name
        required = self.required
        parameters: Dict[str, Any]

        if isinstance(self.parameters, TagParameters):
            parameters = self.parameters.to_dict()

        elif isinstance(self.parameters, UserParameters):
            parameters = self.parameters.to_dict()

        else:
            parameters = self.parameters.to_dict()



        description = self.description

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "type": type,
            "key": key,
            "name": name,
            "required": required,
            "parameters": parameters,
        })
        if description is not UNSET:
            field_dict["description"] = description

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.sheet_parameters import SheetParameters
        from ..models.tag_parameters import TagParameters
        from ..models.user_parameters import UserParameters
        d = src_dict.copy()
        type = AnnotationFieldType(d.pop("type"))




        key = d.pop("key")

        name = d.pop("name")

        required = d.pop("required")

        def _parse_parameters(data: object) -> Union['SheetParameters', 'TagParameters', 'UserParameters']:
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                parameters_type_0 = TagParameters.from_dict(data)



                return parameters_type_0
            except: # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                parameters_type_1 = UserParameters.from_dict(data)



                return parameters_type_1
            except: # noqa: E722
                pass
            if not isinstance(data, dict):
                raise TypeError()
            parameters_type_2 = SheetParameters.from_dict(data)



            return parameters_type_2

        parameters = _parse_parameters(d.pop("parameters"))


        description = d.pop("description", UNSET)

        annotation_field = cls(
            type=type,
            key=key,
            name=name,
            required=required,
            parameters=parameters,
            description=description,
        )

        annotation_field.additional_properties = d
        return annotation_field

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
