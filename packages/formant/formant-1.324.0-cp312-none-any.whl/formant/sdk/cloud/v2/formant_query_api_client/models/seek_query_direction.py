from enum import Enum


class SeekQueryDirection(str, Enum):
    NEXT = "next"
    PREVIOUS = "previous"

    def __str__(self) -> str:
        return str(self.value)
