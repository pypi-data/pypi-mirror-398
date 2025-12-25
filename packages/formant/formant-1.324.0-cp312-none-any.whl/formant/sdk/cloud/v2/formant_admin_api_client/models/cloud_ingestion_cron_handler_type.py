from enum import Enum


class CloudIngestionCronHandlerType(str, Enum):
    LAMBDA = "lambda"

    def __str__(self) -> str:
        return str(self.value)
