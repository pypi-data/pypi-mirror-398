from typing import Dict, List, Optional


class AnnotationField:
    def __init__(
        self, annotation_field  # type: Dict
    ):
        self.type = annotation_field["type"]  # type: str
        self.key = annotation_field["key"]  # type: str
        self.name = annotation_field["name"]  # type: str
        self.description = annotation_field.get(
            "description", None
        )  # type: Optional[str]
        self.required = annotation_field["required"]  # type: bool
        parameters = annotation_field.get("parameters", {})

        # The below value is set if type == tag
        self.tag_choices = parameters.get("choices", None)  # type: Optional[List[str]]

        # The below values are set if type == sheet
        self.url = parameters.get("url", None)  # type: Optional[str]
        self.spreadsheet_id = parameters.get(
            "spreadsheetId", None
        )  # type: Optional[str]
        self.range = parameters.get("range", None)  # type: Optional[str]
