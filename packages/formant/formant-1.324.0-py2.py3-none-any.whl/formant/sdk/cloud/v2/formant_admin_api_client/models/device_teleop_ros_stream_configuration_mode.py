from enum import Enum


class DeviceTeleopRosStreamConfigurationMode(str, Enum):
    COMMAND = "command"
    OBSERVE = "observe"

    def __str__(self) -> str:
        return str(self.value)
