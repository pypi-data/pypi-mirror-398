from enum import Enum


class TeleopJoystickConfigurationPosition(str, Enum):
    LEFT = "left"
    RIGHT = "right"

    def __str__(self) -> str:
        return str(self.value)
