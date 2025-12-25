from enum import Enum


class BatteryEventTriggerConditionType(str, Enum):
    BATTERY = "battery"

    def __str__(self) -> str:
        return str(self.value)
