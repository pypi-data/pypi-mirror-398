from enum import Enum


class ChallengeType(str, Enum):
    NEW_PASSWORD_REQUIRED = "new-password-required"

    def __str__(self) -> str:
        return str(self.value)
