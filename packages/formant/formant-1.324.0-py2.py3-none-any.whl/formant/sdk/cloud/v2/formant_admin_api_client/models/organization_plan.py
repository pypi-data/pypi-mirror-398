from enum import Enum


class OrganizationPlan(str, Enum):
    SELF_SERVE = "self-serve"
    PAID = "paid"

    def __str__(self) -> str:
        return str(self.value)
