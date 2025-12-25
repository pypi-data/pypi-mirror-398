from enum import Enum


class ThresholdEventTriggerConditionType(str, Enum):
    THRESHOLD = "threshold"

    def __str__(self) -> str:
        return str(self.value)
