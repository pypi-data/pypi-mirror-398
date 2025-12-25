from enum import Enum


class UserRegion(str, Enum):
    AMER = "AMER"
    EMEA = "EMEA"
    JAPAC = "JAPAC"

    def __str__(self) -> str:
        return str(self.value)
