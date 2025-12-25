from enum import Enum


class DeviceStreamHardwareConfigurationType(str, Enum):
    HARDWARE = "hardware"

    def __str__(self) -> str:
        return str(self.value)
