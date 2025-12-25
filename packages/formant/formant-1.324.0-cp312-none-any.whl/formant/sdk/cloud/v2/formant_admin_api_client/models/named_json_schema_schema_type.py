from enum import Enum


class NamedJsonSchemaSchemaType(str, Enum):
    CUSTOM_MODULE_CONFIGURATION = "custom-module-configuration"

    def __str__(self) -> str:
        return str(self.value)
