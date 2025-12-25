from enum import Enum


class DeviceType(str, Enum):
    DEFAULT = "default"
    CAPTURE = "capture"

    def __str__(self) -> str:
        return str(self.value)
