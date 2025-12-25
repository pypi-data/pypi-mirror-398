from enum import Enum


class JoystickConfigurationAngular(str, Enum):
    X = "x"
    Y = "y"
    Z = "z"

    def __str__(self) -> str:
        return str(self.value)
