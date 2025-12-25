from typing import Dict
from .annotation_template import AnnotationTemplate


class AnnotationTemplateListResult:
    def __init__(
        self,
        annotation_template_list_result,  # type: Dict
        enabled_only=True,
    ):
        self._template_map = {
            template["name"]: AnnotationTemplate(template)
            for template in annotation_template_list_result["items"]
        }
        self._enabled_only = enabled_only

    def get_by_name(
        self, name  # type:str
    ):
        template = self._template_map.get(name, None)
        if template is None or (not template.enabled and self._enabled_only):
            return None
        return template

    def get_templates(self):
        return list(
            filter(
                lambda template: template.enabled if self._enabled_only else True,
                self._template_map.values(),
            )
        )
