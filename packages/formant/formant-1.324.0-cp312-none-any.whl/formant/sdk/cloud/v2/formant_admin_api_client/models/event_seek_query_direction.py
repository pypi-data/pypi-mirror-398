from enum import Enum


class EventSeekQueryDirection(str, Enum):
    NEXT = "next"
    PREVIOUS = "previous"

    def __str__(self) -> str:
        return str(self.value)
