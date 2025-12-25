from enum import Enum


class DeviceStreamFileTailConfigurationFileFormat(str, Enum):
    PLAIN_TEXT = "plain-text"
    JSON = "json"

    def __str__(self) -> str:
        return str(self.value)
