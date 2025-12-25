from enum import Enum


class DeviceTeleopHardwareStreamConfigurationMode(str, Enum):
    COMMAND = "command"
    OBSERVE = "observe"

    def __str__(self) -> str:
        return str(self.value)
