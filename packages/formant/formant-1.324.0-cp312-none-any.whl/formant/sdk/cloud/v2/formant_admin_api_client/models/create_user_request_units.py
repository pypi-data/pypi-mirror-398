from enum import Enum


class CreateUserRequestUnits(str, Enum):
    METRIC = "metric"
    IMPERIAL = "imperial"

    def __str__(self) -> str:
        return str(self.value)
