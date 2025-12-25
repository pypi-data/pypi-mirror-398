from enum import Enum


class KeyringFilterAuthType(str, Enum):
    OAUTH = "oauth"

    def __str__(self) -> str:
        return str(self.value)
