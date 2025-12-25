from enum import Enum


class ActiveDevicesQueryType(str, Enum):
    DEFAULT = "default"
    CAPTURE = "capture"

    def __str__(self) -> str:
        return str(self.value)
