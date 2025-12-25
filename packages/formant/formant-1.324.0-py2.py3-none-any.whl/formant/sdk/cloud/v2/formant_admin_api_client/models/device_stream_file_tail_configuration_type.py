from enum import Enum


class DeviceStreamFileTailConfigurationType(str, Enum):
    FILE_TAIL = "file-tail"

    def __str__(self) -> str:
        return str(self.value)
