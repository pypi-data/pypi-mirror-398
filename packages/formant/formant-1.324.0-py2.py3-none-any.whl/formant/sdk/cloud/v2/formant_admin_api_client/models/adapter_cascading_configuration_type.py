from enum import Enum


class AdapterCascadingConfigurationType(str, Enum):
    ADAPTER = "adapter"
    VIEW = "view"

    def __str__(self) -> str:
        return str(self.value)
