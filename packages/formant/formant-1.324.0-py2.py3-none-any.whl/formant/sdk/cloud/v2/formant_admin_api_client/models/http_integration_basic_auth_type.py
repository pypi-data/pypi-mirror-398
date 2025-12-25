from enum import Enum


class HttpIntegrationBasicAuthType(str, Enum):
    BASIC = "basic"

    def __str__(self) -> str:
        return str(self.value)
