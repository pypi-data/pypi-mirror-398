from enum import Enum


class EmailConfigurationEmailType(str, Enum):
    SIGN_UP = "sign-up"
    PASSWORD_RESET = "password-reset"

    def __str__(self) -> str:
        return str(self.value)
