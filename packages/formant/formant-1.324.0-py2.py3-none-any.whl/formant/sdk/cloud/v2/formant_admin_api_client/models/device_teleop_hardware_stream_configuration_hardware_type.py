from enum import Enum


class DeviceTeleopHardwareStreamConfigurationHardwareType(str, Enum):
    IP = "ip"
    USB = "usb"

    def __str__(self) -> str:
        return str(self.value)
