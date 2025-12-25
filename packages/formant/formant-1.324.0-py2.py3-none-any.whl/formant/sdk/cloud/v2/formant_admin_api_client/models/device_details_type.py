from enum import Enum


class DeviceDetailsType(str, Enum):
    DEFAULT = "default"
    CAPTURE = "capture"

    def __str__(self) -> str:
        return str(self.value)
