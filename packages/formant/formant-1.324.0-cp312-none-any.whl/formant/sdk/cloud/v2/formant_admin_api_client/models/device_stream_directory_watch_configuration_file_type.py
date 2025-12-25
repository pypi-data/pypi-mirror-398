from enum import Enum


class DeviceStreamDirectoryWatchConfigurationFileType(str, Enum):
    FILE = "file"
    IMAGE = "image"
    VIDEO = "video"
    POINT_CLOUD = "point-cloud"

    def __str__(self) -> str:
        return str(self.value)
