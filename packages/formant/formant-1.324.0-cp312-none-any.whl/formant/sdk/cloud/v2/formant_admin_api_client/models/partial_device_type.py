from enum import Enum


class PartialDeviceType(str, Enum):
    DEFAULT = "default"
    CAPTURE = "capture"

    def __str__(self) -> str:
        return str(self.value)
