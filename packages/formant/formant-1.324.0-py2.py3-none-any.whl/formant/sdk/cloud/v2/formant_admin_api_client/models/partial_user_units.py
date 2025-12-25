from enum import Enum


class PartialUserUnits(str, Enum):
    METRIC = "metric"
    IMPERIAL = "imperial"

    def __str__(self) -> str:
        return str(self.value)
