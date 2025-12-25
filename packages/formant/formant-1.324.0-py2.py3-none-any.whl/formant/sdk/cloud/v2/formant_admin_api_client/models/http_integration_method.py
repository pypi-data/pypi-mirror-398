from enum import Enum


class HttpIntegrationMethod(str, Enum):
    POST = "POST"
    GET = "GET"

    def __str__(self) -> str:
        return str(self.value)
