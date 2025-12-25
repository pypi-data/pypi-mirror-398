from enum import Enum


class BatteryEventTriggerConditionOperator(str, Enum):
    ANY = "any"
    ALL = "all"

    def __str__(self) -> str:
        return str(self.value)
