from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar

import attr

if TYPE_CHECKING:
  from ..models.annotation_field_value_tags import AnnotationFieldValueTags




T = TypeVar("T", bound="AnnotationFieldValue")

@attr.s(auto_attribs=True)
class AnnotationFieldValue:
    """
    Attributes:
        key (str):
        value (str):
        tags (AnnotationFieldValueTags):
    """

    key: str
    value: str
    tags: 'AnnotationFieldValueTags'
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        key = self.key
        value = self.value
        tags = self.tags.to_dict()


        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "key": key,
            "value": value,
            "tags": tags,
        })

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.annotation_field_value_tags import \
            AnnotationFieldValueTags
        d = src_dict.copy()
        key = d.pop("key")

        value = d.pop("value")

        tags = AnnotationFieldValueTags.from_dict(d.pop("tags"))




        annotation_field_value = cls(
            key=key,
            value=value,
            tags=tags,
        )

        annotation_field_value.additional_properties = d
        return annotation_field_value

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
