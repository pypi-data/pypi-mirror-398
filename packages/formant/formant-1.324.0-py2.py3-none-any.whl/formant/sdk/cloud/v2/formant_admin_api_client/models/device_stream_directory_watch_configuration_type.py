from enum import Enum


class DeviceStreamDirectoryWatchConfigurationType(str, Enum):
    DIRECTORY_WATCH = "directory-watch"

    def __str__(self) -> str:
        return str(self.value)
