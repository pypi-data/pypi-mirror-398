from enum import Enum


class AnnotationFieldType(str, Enum):
    TAG = "tag"
    SHEET = "sheet"
    USER = "user"

    def __str__(self) -> str:
        return str(self.value)
