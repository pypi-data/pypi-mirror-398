from enum import Enum


class UserSmsOptInStatus(str, Enum):
    OPT_IN = "OPT_IN"
    OPT_OUT = "OPT_OUT"

    def __str__(self) -> str:
        return str(self.value)
