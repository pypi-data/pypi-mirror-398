from enum import Enum


class ImageViewConfigurationMode(str, Enum):
    DEVICE = "device"
    TIME = "time"

    def __str__(self) -> str:
        return str(self.value)
