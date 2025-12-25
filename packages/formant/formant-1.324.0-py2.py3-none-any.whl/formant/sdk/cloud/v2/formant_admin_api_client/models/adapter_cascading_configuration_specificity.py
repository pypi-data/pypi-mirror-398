from enum import Enum


class AdapterCascadingConfigurationSpecificity(str, Enum):
    GLOBAL = "global"
    DEVICE = "device"

    def __str__(self) -> str:
        return str(self.value)
