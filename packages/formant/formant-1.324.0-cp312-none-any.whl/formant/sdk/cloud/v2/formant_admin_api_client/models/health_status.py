from enum import Enum


class HealthStatus(str, Enum):
    UNKNOWN = "unknown"
    OPERATIONAL = "operational"
    OFFLINE = "offline"
    ERROR = "error"

    def __str__(self) -> str:
        return str(self.value)
