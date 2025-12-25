from enum import Enum


class DeviceStreamHardwareConfigurationQuality(str, Enum):
    VALUE_0 = "1080p"
    VALUE_1 = "720p"
    VALUE_2 = "480p"
    VALUE_3 = "360p"

    def __str__(self) -> str:
        return str(self.value)
