from enum import Enum


class RegexEventTriggerConditionType(str, Enum):
    REGEX = "regex"

    def __str__(self) -> str:
        return str(self.value)
