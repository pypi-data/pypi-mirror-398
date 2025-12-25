from enum import Enum


class UserParametersRolesItem(str, Enum):
    VIEWER = "viewer"
    OPERATOR = "operator"
    ADMINISTRATOR = "administrator"

    def __str__(self) -> str:
        return str(self.value)
