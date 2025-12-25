from enum import Enum


class OrganizationSupportTier(str, Enum):
    STANDARD = "standard"
    ENTERPRISE = "enterprise"

    def __str__(self) -> str:
        return str(self.value)
