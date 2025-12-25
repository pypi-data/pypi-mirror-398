from enum import Enum


class SsoConfigurationAuthenticationFlow(str, Enum):
    OIDC = "oidc"
    GOOGLE = "google"

    def __str__(self) -> str:
        return str(self.value)
