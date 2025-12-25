from enum import Enum


class BitsetEventTriggerConditionType(str, Enum):
    BITSET = "bitset"

    def __str__(self) -> str:
        return str(self.value)
