from enum import Enum


class HttpIntegrationNoAuthType(str, Enum):
    NONE = "none"

    def __str__(self) -> str:
        return str(self.value)
