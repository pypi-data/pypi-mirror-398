from enum import Enum


class TeleopJoystickAxisConfigurationDimension(str, Enum):
    LINEAR_X = "linear-x"
    LINEAR_Y = "linear-y"
    LINEAR_Z = "linear-z"
    ANGULAR_X = "angular-x"
    ANGULAR_Y = "angular-y"
    ANGULAR_Z = "angular-z"

    def __str__(self) -> str:
        return str(self.value)
