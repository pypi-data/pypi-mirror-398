from enum import Enum


class UserLanguage(str, Enum):
    EN_US = "en-US"
    FR_CA = "fr-CA"

    def __str__(self) -> str:
        return str(self.value)
