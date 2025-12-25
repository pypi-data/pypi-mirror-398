from typing import Dict, List
from .annotation_field import AnnotationField


class AnnotationTemplate:
    def __init__(
        self, annotation_template_response  # type: Dict
    ):
        self.id = annotation_template_response["id"]  # type: str
        self.name = annotation_template_response["name"]  # type: str
        self.description = annotation_template_response["description"]  # type: str
        self.enabled = annotation_template_response["enabled"]  # type: str
        self.fields = list(
            map(
                lambda field: AnnotationField(field),
                annotation_template_response["fields"],
            )
        )  # type: List[AnnotationField]

    def get_required_tag_fields(self):
        return list(
            filter(lambda field: field.required and field.type == "tag", self.fields)
        )
