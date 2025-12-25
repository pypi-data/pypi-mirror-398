from enum import Enum


class PresenceEventTriggerConditionType(str, Enum):
    PRESENCE = "presence"

    def __str__(self) -> str:
        return str(self.value)
