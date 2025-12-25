from enum import Enum


class DeviceTeleopCustomStreamConfigurationMode(str, Enum):
    COMMAND = "command"
    OBSERVE = "observe"

    def __str__(self) -> str:
        return str(self.value)
