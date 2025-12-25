from enum import Enum


class DeviceStreamHardwareConfigurationHardwareType(str, Enum):
    IP = "ip"
    USB = "usb"

    def __str__(self) -> str:
        return str(self.value)
