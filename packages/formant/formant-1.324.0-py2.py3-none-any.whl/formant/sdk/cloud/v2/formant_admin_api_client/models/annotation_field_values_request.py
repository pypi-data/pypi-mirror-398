from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar

import attr

if TYPE_CHECKING:
  from ..models.annotation_field_values_request_tags import \
      AnnotationFieldValuesRequestTags




T = TypeVar("T", bound="AnnotationFieldValuesRequest")

@attr.s(auto_attribs=True)
class AnnotationFieldValuesRequest:
    """
    Attributes:
        annotation_template_id (str):
        key (Any):
        tags (AnnotationFieldValuesRequestTags):
    """

    annotation_template_id: str
    key: Any
    tags: 'AnnotationFieldValuesRequestTags'
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        annotation_template_id = self.annotation_template_id
        key = self.key
        tags = self.tags.to_dict()


        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "annotationTemplateId": annotation_template_id,
            "key": key,
            "tags": tags,
        })

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.annotation_field_values_request_tags import \
            AnnotationFieldValuesRequestTags
        d = src_dict.copy()
        annotation_template_id = d.pop("annotationTemplateId")

        key = d.pop("key")

        tags = AnnotationFieldValuesRequestTags.from_dict(d.pop("tags"))




        annotation_field_values_request = cls(
            annotation_template_id=annotation_template_id,
            key=key,
            tags=tags,
        )

        annotation_field_values_request.additional_properties = d
        return annotation_field_values_request

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
