from enum import Enum


class PartialHttpIntegrationMethod(str, Enum):
    POST = "POST"
    GET = "GET"

    def __str__(self) -> str:
        return str(self.value)
