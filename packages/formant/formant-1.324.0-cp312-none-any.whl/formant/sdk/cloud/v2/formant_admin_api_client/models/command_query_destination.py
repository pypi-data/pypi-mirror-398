from enum import Enum


class CommandQueryDestination(str, Enum):
    AGENT = "agent"
    CLOUD = "cloud"

    def __str__(self) -> str:
        return str(self.value)
