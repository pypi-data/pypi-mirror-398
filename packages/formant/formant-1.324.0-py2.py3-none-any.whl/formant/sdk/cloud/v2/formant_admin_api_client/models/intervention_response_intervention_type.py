from enum import Enum


class InterventionResponseInterventionType(str, Enum):
    SELECTION = "selection"
    LABELING = "labeling"
    TELEOP = "teleop"
    PHYSICAL = "physical"

    def __str__(self) -> str:
        return str(self.value)
