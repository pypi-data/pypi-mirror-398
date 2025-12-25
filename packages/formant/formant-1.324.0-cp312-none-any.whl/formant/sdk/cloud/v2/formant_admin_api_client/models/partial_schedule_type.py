from enum import Enum


class PartialScheduleType(str, Enum):
    COMMAND = "command"
    RUN_WORKFLOW = "run-workflow"
    GENERATE_INSIGHTS = "generate-insights"
    COMPOSE_OPERATION = "compose-operation"

    def __str__(self) -> str:
        return str(self.value)
