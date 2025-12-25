from enum import Enum


class DeviceTeleopRosStreamConfigurationNumericControlVisualization(str, Enum):
    SLIDER = "slider"
    DIAL = "dial"

    def __str__(self) -> str:
        return str(self.value)
