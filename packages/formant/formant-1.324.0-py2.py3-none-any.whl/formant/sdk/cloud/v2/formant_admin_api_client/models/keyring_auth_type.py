from enum import Enum


class KeyringAuthType(str, Enum):
    OAUTH = "oauth"

    def __str__(self) -> str:
        return str(self.value)
