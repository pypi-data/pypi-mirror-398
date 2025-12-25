from enum import Enum


class CreateInterventionResponseType(str, Enum):
    INTERVENTION_RESPONSE = "intervention-response"

    def __str__(self) -> str:
        return str(self.value)
