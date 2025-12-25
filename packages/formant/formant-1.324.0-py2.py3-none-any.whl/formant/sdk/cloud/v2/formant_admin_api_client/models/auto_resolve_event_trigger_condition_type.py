from enum import Enum


class AutoResolveEventTriggerConditionType(str, Enum):
    AUTO_RESOLVE = "auto-resolve"

    def __str__(self) -> str:
        return str(self.value)
