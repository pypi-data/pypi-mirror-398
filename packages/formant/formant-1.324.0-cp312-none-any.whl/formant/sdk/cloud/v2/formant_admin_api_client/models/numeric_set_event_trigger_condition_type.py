from enum import Enum


class NumericSetEventTriggerConditionType(str, Enum):
    NUMERIC_SET = "numeric set"

    def __str__(self) -> str:
        return str(self.value)
