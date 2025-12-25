from enum import Enum


class DeviceTeleopRosStreamConfigurationAudioCodec(str, Enum):
    RAW = "raw"

    def __str__(self) -> str:
        return str(self.value)
